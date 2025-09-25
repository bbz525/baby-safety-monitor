#!/usr/bin/env python3
"""
远程Vision服务
支持摄像头远程访问和检测
"""

import cv2
import threading
import time
import json
import base64
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
import io

app = FastAPI(title="Remote Vision Service", version="0.1.0")

class CameraType(str, Enum):
    RTSP = "rtsp"
    HTTP = "http"
    FILE = "file"
    MAC_CAMERA = "mac_camera"

class CameraStatus(str, Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"

class CameraConfig(BaseModel):
    id: Optional[str] = None
    name: str
    source: str
    type: CameraType
    enabled: bool = True
    fps: float = 1.0
    resolution: int = 640
    status: CameraStatus = CameraStatus.STOPPED
    last_error: Optional[str] = None

class CameraManager:
    def __init__(self):
        self.cameras = {}
        self.active_cameras = {}
    
    def add_camera(self, config: CameraConfig) -> CameraConfig:
        import uuid
        config.id = config.id or str(uuid.uuid4())
        self.cameras[config.id] = config
        return config
    
    def start_camera(self, camera_id: str) -> bool:
        if camera_id not in self.cameras:
            return False
        
        camera = self.cameras[camera_id]
        
        # 打开摄像头
        if camera.type == CameraType.MAC_CAMERA:
            cap = cv2.VideoCapture(int(camera.source))
        else:
            cap = cv2.VideoCapture(camera.source)
        
        if not cap.isOpened():
            camera.status = CameraStatus.ERROR
            camera.last_error = "无法打开摄像头"
            return False
        
        # 设置参数
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera.resolution)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera.resolution)
        cap.set(cv2.CAP_PROP_FPS, camera.fps)
        
        self.active_cameras[camera_id] = cap
        camera.status = CameraStatus.RUNNING
        camera.last_error = None
        
        return True
    
    def stop_camera(self, camera_id: str) -> bool:
        if camera_id in self.active_cameras:
            self.active_cameras[camera_id].release()
            del self.active_cameras[camera_id]
        
        if camera_id in self.cameras:
            self.cameras[camera_id].status = CameraStatus.STOPPED
        
        return True
    
    def get_frame(self, camera_id: str):
        if camera_id not in self.active_cameras:
            return None
        
        cap = self.active_cameras[camera_id]
        ret, frame = cap.read()
        return frame if ret else None

# 全局摄像头管理器
camera_manager = CameraManager()

@app.get("/")
async def root():
    """主页"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>远程Vision服务</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .camera-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .camera-card { border: 1px solid #ddd; border-radius: 8px; padding: 15px; }
            .camera-stream { width: 100%; max-width: 300px; }
            .status { padding: 5px 10px; border-radius: 4px; color: white; }
            .status.running { background: #28a745; }
            .status.stopped { background: #6c757d; }
            .status.error { background: #dc3545; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>远程Vision服务</h1>
            <div id="cameras"></div>
        </div>
        <script>
            async function loadCameras() {
                try {
                    const response = await fetch('/cameras');
                    const cameras = await response.json();
                    
                    const container = document.getElementById('cameras');
                    container.innerHTML = '<div class="camera-grid">';
                    
                    cameras.forEach(camera => {
                        const card = document.createElement('div');
                        card.className = 'camera-card';
                        card.innerHTML = `
                            <h3>${camera.name}</h3>
                            <p>类型: ${camera.type}</p>
                            <p>状态: <span class="status ${camera.status}">${camera.status}</span></p>
                            <p>分辨率: ${camera.resolution}px</p>
                            <p>帧率: ${camera.fps} FPS</p>
                            <img class="camera-stream" src="/stream/${camera.id}" alt="${camera.name}">
                            <div>
                                <button onclick="startCamera('${camera.id}')">启动</button>
                                <button onclick="stopCamera('${camera.id}')">停止</button>
                            </div>
                        `;
                        container.querySelector('.camera-grid').appendChild(card);
                    });
                    
                    container.innerHTML += '</div>';
                } catch (error) {
                    console.error('加载摄像头失败:', error);
                }
            }
            
            async function startCamera(cameraId) {
                try {
                    await fetch(`/cameras/${cameraId}/start`, { method: 'POST' });
                    loadCameras();
                } catch (error) {
                    console.error('启动摄像头失败:', error);
                }
            }
            
            async function stopCamera(cameraId) {
                try {
                    await fetch(`/cameras/${cameraId}/stop`, { method: 'POST' });
                    loadCameras();
                } catch (error) {
                    console.error('停止摄像头失败:', error);
                }
            }
            
            // 页面加载时获取摄像头列表
            loadCameras();
            
            // 每5秒刷新一次
            setInterval(loadCameras, 5000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/health")
def health():
    return {"status": "ok", "service": "remote-vision"}

@app.get("/cameras", response_model=List[CameraConfig])
def list_cameras():
    """列出所有摄像头"""
    return list(camera_manager.cameras.values())

@app.post("/cameras", response_model=CameraConfig)
def create_camera(config: CameraConfig):
    """创建新摄像头"""
    return camera_manager.add_camera(config)

@app.get("/cameras/{camera_id}", response_model=CameraConfig)
def get_camera(camera_id: str):
    """获取指定摄像头"""
    if camera_id not in camera_manager.cameras:
        raise HTTPException(status_code=404, detail="摄像头不存在")
    return camera_manager.cameras[camera_id]

@app.post("/cameras/{camera_id}/start")
def start_camera(camera_id: str):
    """启动摄像头"""
    if camera_manager.start_camera(camera_id):
        return {"started": True}
    else:
        raise HTTPException(status_code=400, detail="启动失败")

@app.post("/cameras/{camera_id}/stop")
def stop_camera(camera_id: str):
    """停止摄像头"""
    camera_manager.stop_camera(camera_id)
    return {"stopped": True}

@app.get("/stream/{camera_id}")
def stream_camera(camera_id: str):
    """摄像头视频流"""
    def generate_frames():
        while True:
            frame = camera_manager.get_frame(camera_id)
            if frame is None:
                break
            
            # 调整大小
            frame = cv2.resize(frame, (640, 480))
            
            # 编码为JPEG
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            
            # 发送帧
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            
            time.sleep(0.033)  # ~30 FPS
    
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/api/cameras/{camera_id}/frame")
def get_camera_frame(camera_id: str):
    """获取摄像头单帧（JSON格式）"""
    frame = camera_manager.get_frame(camera_id)
    if frame is None:
        raise HTTPException(status_code=404, detail="无法获取帧")
    
    # 调整大小
    frame = cv2.resize(frame, (320, 240))
    
    # 编码为JPEG
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
    
    # 转换为base64
    frame_base64 = base64.b64encode(buffer).decode('utf-8')
    
    return {
        "camera_id": camera_id,
        "timestamp": time.time(),
        "frame": frame_base64,
        "format": "jpeg"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
