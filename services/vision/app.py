import os
import uuid
import asyncio
import threading
import time
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

import httpx
import cv2
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import shutil
from pydantic import BaseModel
from ultralytics import YOLO
import tempfile


BACKEND_BASE = os.getenv("BACKEND_BASE", "http://backend:8080")

app = FastAPI(title="Vision Service", version="0.3.0")


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
        if camera_id in self.stop_events:
            self.stop_events[camera_id].set()
        
        if camera_id in self.capture_threads:
            thread = self.capture_threads[camera_id]
            thread.join(timeout=5.0)
            del self.capture_threads[camera_id]
        
        if camera_id in self.stop_events:
            del self.stop_events[camera_id]
        
        if camera_id in self.cameras:
            self.cameras[camera_id].status = CameraStatus.STOPPED
        
        return True
    
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
            if cap:
                cap.release()
    
    def _process_frame(self, camera_id: str, frame):
        try:
            camera = self.cameras[camera_id]
            model = self.get_model()
            
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
            
            # 保存当前帧
            os.makedirs("/app/data", exist_ok=True)
            cv2.imwrite("/app/data/last.jpg", frame)
            
            # 处理检测结果
            for box in res.boxes:
                cls_id = int(box.cls.item()) if box.cls is not None else -1
                xywh = box.xywh.cpu().numpy().astype(int).tolist()[0]
                x_center, y_center, w, h = xywh
                x = max(0, int(x_center - w / 2))
                y = max(0, int(y_center - h / 2))
                conf = float(box.conf.item()) if box.conf is not None else 0.0
                
                # 只处理人员检测
                if cls_id == 0:  # COCO person class
                    event = VisionEvent(
                        trackId=f"{camera_id}-{uuid.uuid4().hex[:8]}",
                        bbox=[x, y, int(w), int(h)],
                        action="detected",
                        riskScore=min(0.99, 1.0 - (1.0 - conf) * 0.5),
                    )
                    self._emit_event(event)
                    break  # 只发送第一个检测到的人员
                    
        except Exception as e:
            print(f"处理帧时出错: {e}")
    
    def _emit_event(self, event: VisionEvent):
        try:
            url = f"{BACKEND_BASE}/api/events/vision"
            with httpx.Client(timeout=5.0) as client:
                r = client.post(url, json=event.model_dump())
                r.raise_for_status()
        except Exception as e:
            print(f"发送事件失败: {e}")


# 全局摄像头管理器
camera_manager = CameraManager()


@app.get("/health")
def health():
    return {"status": "ok", "backend": BACKEND_BASE}


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