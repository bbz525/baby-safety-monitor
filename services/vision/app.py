import os
import uuid
import asyncio
import threading
import time
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
import logging

import httpx
import cv2
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import shutil
from pydantic import BaseModel
from ultralytics import YOLO
import tempfile
import queue
import numpy as np


BACKEND_BASE = os.getenv("BACKEND_BASE", "http://backend:8080")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 性能指标
class PerformanceMetrics:
    def __init__(self):
        self.total_frames = 0
        self.total_detections = 0
        self.total_errors = 0
        self.start_time = time.time()
        self.last_fps_time = time.time()
        self.last_frame_count = 0
        
    def record_frame(self):
        self.total_frames += 1
        
    def record_detection(self):
        self.total_detections += 1
        
    def record_error(self):
        self.total_errors += 1
        
    def get_fps(self):
        current_time = time.time()
        time_diff = current_time - self.last_fps_time
        if time_diff >= 1.0:  # 每秒计算一次
            frame_diff = self.total_frames - self.last_frame_count
            fps = frame_diff / time_diff
            self.last_fps_time = current_time
            self.last_frame_count = self.total_frames
            return fps
        return 0
        
    def get_stats(self):
        uptime = time.time() - self.start_time
        return {
            "uptime_seconds": uptime,
            "total_frames": self.total_frames,
            "total_detections": self.total_detections,
            "total_errors": self.total_errors,
            "avg_fps": self.total_frames / uptime if uptime > 0 else 0,
            "detection_rate": self.total_detections / self.total_frames if self.total_frames > 0 else 0
        }

metrics = PerformanceMetrics()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化
    logger.info("Vision 服务启动中...")
    
    # 初始化线程池
    camera_manager.thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="vision-worker")
    
    yield
    
    # 关闭时清理
    logger.info("Vision 服务关闭中...")
    
    # 停止所有摄像头
    for camera_id in list(camera_manager.cameras.keys()):
        camera_manager.stop_camera(camera_id)
    
    # 关闭线程池
    if camera_manager.thread_pool:
        camera_manager.thread_pool.shutdown(wait=True)
    
    logger.info("Vision 服务已关闭")

app = FastAPI(title="Vision Service", version="0.4.0", lifespan=lifespan)


class CameraStatus(str, Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"


class CameraType(str, Enum):
    RTSP = "rtsp"
    HTTP = "http"
    FILE = "file"
    MAC_CAMERA = "mac_camera"


class CameraConfig(BaseModel):
    id: Optional[str] = None
    name: str
    source: str
    type: CameraType
    enabled: bool = True
    fps: float = 1.0  # 采样帧率
    resolution: int = 640
    status: CameraStatus = CameraStatus.STOPPED
    last_error: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class VisionEvent(BaseModel):
    timestamp: Optional[str] = None
    trackId: str
    bbox: List[int]
    action: Optional[str] = None
    riskScore: Optional[float] = None


class CameraManager:
    def __init__(self):
        self.cameras: Dict[str, CameraConfig] = {}
        self.capture_threads: Dict[str, threading.Thread] = {}
        self.stop_events: Dict[str, threading.Event] = {}
        self.model: Optional[YOLO] = None
        self.thread_pool: Optional[ThreadPoolExecutor] = None
        self.http_client: Optional[httpx.Client] = None
        self.frame_queue = queue.Queue(maxsize=100)  # 帧缓冲队列
        
    def get_http_client(self) -> httpx.Client:
        """@获取HTTP客户端（连接池）"""
        if self.http_client is None:
            self.http_client = httpx.Client(
                timeout=10.0,
                limits=httpx.Limits(
                    max_keepalive_connections=20,
                    max_connections=100,
                    keepalive_expiry=30.0
                )
            )
        return self.http_client
        
    def get_model(self) -> YOLO:
        if self.model is None:
            weights = os.getenv("YOLO_WEIGHTS", "yolov8n.pt")
            self.model = YOLO(weights)
        return self.model
    
    def add_camera(self, config: CameraConfig) -> CameraConfig:
        config.id = config.id or str(uuid.uuid4())
        config.created_at = datetime.now()
        config.updated_at = datetime.now()
        self.cameras[config.id] = config
        return config
    
    def update_camera(self, camera_id: str, **updates) -> Optional[CameraConfig]:
        if camera_id not in self.cameras:
            return None
        camera = self.cameras[camera_id]
        for key, value in updates.items():
            if hasattr(camera, key):
                setattr(camera, key, value)
        camera.updated_at = datetime.now()
        return camera
    
    def delete_camera(self, camera_id: str) -> bool:
        if camera_id in self.cameras:
            self.stop_camera(camera_id)
            del self.cameras[camera_id]
            return True
        return False
    
    def start_camera(self, camera_id: str) -> bool:
        if camera_id not in self.cameras:
            return False
        
        camera = self.cameras[camera_id]
        if camera.status == CameraStatus.RUNNING:
            return True
        
        # 停止现有线程
        self.stop_camera(camera_id)
        
        # 创建停止事件
        stop_event = threading.Event()
        self.stop_events[camera_id] = stop_event
        
        # 创建并启动捕获线程
        thread = threading.Thread(
            target=self._capture_loop,
            args=(camera_id, stop_event),
            daemon=True
        )
        self.capture_threads[camera_id] = thread
        thread.start()
        
        camera.status = CameraStatus.RUNNING
        camera.last_error = None
        return True
    
    def stop_camera(self, camera_id: str) -> bool:
        try:
            # 发出停止信号（非阻塞）
            if camera_id in self.stop_events:
                self.stop_events[camera_id].set()

            # 尽量避免在请求线程中 join，防止阻塞导致服务不可用
            if camera_id in self.capture_threads:
                thread = self.capture_threads[camera_id]
                if thread.is_alive() and threading.current_thread() is not thread:
                    # 在后台短暂等待线程结束，但不阻塞当前请求
                    def _join_target(t: threading.Thread, cid: str):
                        try:
                            t.join(timeout=5.0)
                        except Exception:
                            pass
                        finally:
                            # 安全地清理引用
                            self.capture_threads.pop(cid, None)
                            self.stop_events.pop(cid, None)

                    threading.Thread(target=_join_target, args=(thread, camera_id), daemon=True).start()
                else:
                    # 无需等待，直接清理引用
                    self.capture_threads.pop(camera_id, None)
                    self.stop_events.pop(camera_id, None)

            # 更新状态
            if camera_id in self.cameras:
                self.cameras[camera_id].status = CameraStatus.STOPPED
                self.cameras[camera_id].last_error = None

            return True
        except Exception:
            # 任何异常都不应影响服务稳定性
            if camera_id in self.cameras:
                self.cameras[camera_id].status = CameraStatus.ERROR
            return False
    
    def _capture_loop(self, camera_id: str, stop_event: threading.Event):
        camera = self.cameras[camera_id]
        cap = None
        
        try:
            # 根据类型创建VideoCapture
            if camera.type == CameraType.RTSP:
                cap = cv2.VideoCapture(camera.source)
            elif camera.type == CameraType.HTTP:
                cap = cv2.VideoCapture(camera.source)
            elif camera.type == CameraType.FILE:
                cap = cv2.VideoCapture(camera.source)
            elif camera.type == CameraType.MAC_CAMERA:
                # Mac摄像头使用数字索引
                try:
                    camera_index = int(camera.source)
                    cap = cv2.VideoCapture(camera_index)
                except ValueError:
                    raise Exception(f"Mac摄像头索引无效: {camera.source}")
            
            if not cap or not cap.isOpened():
                raise Exception(f"无法打开摄像头源: {camera.source}")
            
            # 设置分辨率
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera.resolution)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera.resolution)
            
            frame_interval = 1.0 / camera.fps
            last_frame_time = 0
            
            while not stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    camera.status = CameraStatus.ERROR
                    camera.last_error = "无法读取帧"
                    break
                
                current_time = time.time()
                if current_time - last_frame_time >= frame_interval:
                    # 执行推理
                    self._process_frame(camera_id, frame)
                    last_frame_time = current_time
                
                # 短暂休眠避免CPU占用过高
                time.sleep(0.01)
                
        except Exception as e:
            camera.status = CameraStatus.ERROR
            camera.last_error = str(e)
        finally:
            try:
                if cap:
                    cap.release()
            except Exception:
                pass
    
    def _process_frame(self, camera_id: str, frame):
        try:
            camera = self.cameras[camera_id]
            model = self.get_model()
            
            # 记录性能指标
            metrics.record_frame()
            
            # 执行YOLO推理
            results = model.predict(
                source=frame,
                imgsz=camera.resolution,
                conf=0.25,
                verbose=False
            )
            
            if not results:
                return
            
            res = results[0]
            if res.boxes is None:
                return
            
            # 保存当前帧（异步）
            if self.thread_pool:
                self.thread_pool.submit(self._save_frame, frame)
            else:
                self._save_frame(frame)
            
            # 处理检测结果
            for box in res.boxes:
                cls_id = int(box.cls.item()) if box.cls is not None else -1
                # 安全地处理坐标数据
                try:
                    xywh = box.xywh.cpu().numpy().astype(int).tolist()[0]
                except AttributeError:
                    # 如果没有cpu()方法，直接转换
                    xywh = box.xywh.numpy().astype(int).tolist()[0]
                    
                x_center, y_center, w, h = xywh
                x = max(0, int(x_center - w / 2))
                y = max(0, int(y_center - h / 2))
                conf = float(box.conf.item()) if box.conf is not None else 0.0
                
                # 只处理人员检测
                if cls_id == 0:  # COCO person class
                    metrics.record_detection()
                    event = VisionEvent(
                        trackId=f"{camera_id}-{uuid.uuid4().hex[:8]}",
                        bbox=[x, y, int(w), int(h)],
                        action="detected",
                        riskScore=min(0.99, 1.0 - (1.0 - conf) * 0.5),
                    )
                    # 异步发送事件
                    if self.thread_pool:
                        self.thread_pool.submit(self._emit_event, event)
                    else:
                        self._emit_event(event)
                    break  # 只发送第一个检测到的人员
                    
        except Exception as e:
            metrics.record_error()
            logger.error(f"处理帧时出错: {e}")
    
    def _save_frame(self, frame):
        """@保存帧到文件"""
        try:
            os.makedirs("/app/data", exist_ok=True)
            cv2.imwrite("/app/data/last.jpg", frame)
        except Exception as e:
            logger.error(f"保存帧失败: {e}")
    
    def _emit_event(self, event: VisionEvent):
        """@发送事件到后端"""
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                url = f"{BACKEND_BASE}/api/events/vision"
                client = self.get_http_client()
                response = client.post(url, json=event.model_dump())
                response.raise_for_status()
                logger.debug(f"事件发送成功: {event.trackId}")
                return
            except Exception as e:
                logger.warning(f"发送事件失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))  # 指数退避
                else:
                    metrics.record_error()
                    logger.error(f"发送事件最终失败: {e}")


# 全局摄像头管理器
camera_manager = CameraManager()


@app.get("/health")
def health():
    return {
        "status": "ok", 
        "backend": BACKEND_BASE,
        "metrics": metrics.get_stats(),
        "current_fps": metrics.get_fps(),
        "active_cameras": len([c for c in camera_manager.cameras.values() if c.status == CameraStatus.RUNNING])
    }


@app.get("/metrics")
def get_metrics():
    """@获取详细性能指标"""
    stats = metrics.get_stats()
    stats.update({
        "cameras": {
            "total": len(camera_manager.cameras),
            "running": len([c for c in camera_manager.cameras.values() if c.status == CameraStatus.RUNNING]),
            "stopped": len([c for c in camera_manager.cameras.values() if c.status == CameraStatus.STOPPED]),
            "error": len([c for c in camera_manager.cameras.values() if c.status == CameraStatus.ERROR]),
        },
        "system": {
            "thread_pool_active": camera_manager.thread_pool._threads if camera_manager.thread_pool else 0,
            "capture_threads": len(camera_manager.capture_threads),
        }
    })
    return stats


@app.post("/emit")
def emit(event: VisionEvent):
    url = f"{BACKEND_BASE}/api/events/vision"
    with httpx.Client(timeout=5.0) as client:
        r = client.post(url, json=event.model_dump())
        r.raise_for_status()
    return {"sent": True}


@app.post("/simulate")
def simulate(track_id: str = "t-1", x: int = 100, y: int = 120, w: int = 60, h: int = 80,
             action: str = "walk", risk: float = 0.3):
    e = VisionEvent(trackId=track_id, bbox=[x, y, w, h], action=action, riskScore=risk)
    return emit(e)


# 摄像头管理API
@app.post("/cameras", response_model=CameraConfig)
def create_camera(config: CameraConfig):
    """创建新摄像头"""
    return camera_manager.add_camera(config)


@app.get("/cameras", response_model=List[CameraConfig])
def list_cameras():
    """列出所有摄像头"""
    return list(camera_manager.cameras.values())


@app.get("/cameras/{camera_id}", response_model=CameraConfig)
def get_camera(camera_id: str):
    """获取指定摄像头"""
    if camera_id not in camera_manager.cameras:
        raise HTTPException(status_code=404, detail="摄像头不存在")
    return camera_manager.cameras[camera_id]


@app.put("/cameras/{camera_id}", response_model=CameraConfig)
def update_camera(camera_id: str, config: CameraConfig):
    """更新摄像头配置"""
    if camera_id not in camera_manager.cameras:
        raise HTTPException(status_code=404, detail="摄像头不存在")
    
    updated = camera_manager.update_camera(
        camera_id,
        name=config.name,
        source=config.source,
        type=config.type,
        enabled=config.enabled,
        fps=config.fps,
        resolution=config.resolution
    )
    return updated


@app.delete("/cameras/{camera_id}")
def delete_camera(camera_id: str):
    """删除摄像头"""
    if not camera_manager.delete_camera(camera_id):
        raise HTTPException(status_code=404, detail="摄像头不存在")
    return {"deleted": True}


@app.post("/cameras/{camera_id}/start")
def start_camera(camera_id: str):
    """启动摄像头"""
    if camera_id not in camera_manager.cameras:
        raise HTTPException(status_code=404, detail="摄像头不存在")
    
    if camera_manager.start_camera(camera_id):
        return {"started": True}
    else:
        raise HTTPException(status_code=400, detail="启动失败")


@app.post("/cameras/{camera_id}/stop")
def stop_camera(camera_id: str):
    """停止摄像头"""
    if camera_id not in camera_manager.cameras:
        raise HTTPException(status_code=404, detail="摄像头不存在")
    
    camera_manager.stop_camera(camera_id)
    return {"stopped": True}


# 原有的推理接口
@app.post("/infer")
def infer(
    source_url: Optional[str] = Form(default=None),
    track_id: Optional[str] = Form(default=None),
    file: Optional[UploadFile] = File(default=None),
):
    model = camera_manager.get_model()

    if not source_url and not file:
        return {"error": "provide source_url or file"}

    input_path: Optional[str] = None
    temp_file = None
    try:
        if source_url:
            suffix = os.path.splitext(source_url.split("?")[0])[-1] or ".jpg"
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            with httpx.Client(timeout=15.0, follow_redirects=True) as client:
                r = client.get(source_url)
                r.raise_for_status()
                temp_file.write(r.content)
            temp_file.flush()
            temp_file.close()
            input_path = temp_file.name
        else:
            suffix = os.path.splitext(file.filename or "upload.jpg")[1]
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp_file.write(file.file.read())
            temp_file.flush()
            temp_file.close()
            input_path = temp_file.name

        results = model.predict(source=input_path, imgsz=640, conf=0.25, verbose=False)
        if not results:
            return {"detections": []}

        res = results[0]
        detections = []
        if res.boxes is not None:
            for b in res.boxes:
                cls_id = int(b.cls.item()) if b.cls is not None else -1
                xywh = b.xywh.cpu().numpy().astype(int).tolist()[0]
                x_center, y_center, w, h = xywh
                x = max(0, int(x_center - w / 2))
                y = max(0, int(y_center - h / 2))
                conf = float(b.conf.item()) if b.conf is not None else 0.0
                detections.append({
                    "classId": cls_id,
                    "conf": conf,
                    "bbox": [x, y, int(w), int(h)],
                })

        primary = None
        persons = [d for d in detections if d.get("classId") == 0]
        primary = max(persons or detections, key=lambda d: d.get("conf", 0.0), default=None)

        if primary is None:
            return {"detections": detections, "emitted": False}

        try:
            os.makedirs("/app/data", exist_ok=True)
            shutil.copyfile(input_path, "/app/data/last.jpg")
        except Exception:
            pass

        event = VisionEvent(
            trackId=track_id or f"auto-{uuid.uuid4().hex[:8]}",
            bbox=primary["bbox"],
            action="detected",
            riskScore=min(0.99, 1.0 - (1.0 - float(primary.get("conf", 0.0))) * 0.5),
        )
        emit(event)
        return {"detections": detections, "emitted": True, "event": event.model_dump()}
    except Exception as e:
        return {"error": str(e)}
    finally:
        if temp_file is not None:
            try:
                os.unlink(temp_file.name)
            except Exception:
                pass


@app.get("/last.jpg")
def last_frame():
    path = "/app/data/last.jpg"
    if os.path.exists(path):
        return FileResponse(path, media_type="image/jpeg")
    return {"error": "no image"}


# 启动时清理所有摄像头
@app.on_event("shutdown")
def shutdown_event():
    for camera_id in list(camera_manager.cameras.keys()):
        camera_manager.stop_camera(camera_id)