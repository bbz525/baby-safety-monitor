#!/usr/bin/env python3
"""
简化的Vision服务测试版本
"""

from fastapi import FastAPI
from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

app = FastAPI(title="Vision Test Service", version="0.1.0")

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

# 内存存储
cameras = {}

@app.get("/health")
def health():
    return {"status": "ok", "service": "vision-test"}

@app.get("/cameras", response_model=List[CameraConfig])
def list_cameras():
    """列出所有摄像头"""
    return list(cameras.values())

@app.post("/cameras", response_model=CameraConfig)
def create_camera(config: CameraConfig):
    """创建新摄像头"""
    import uuid
    config.id = config.id or str(uuid.uuid4())
    cameras[config.id] = config
    return config

@app.get("/cameras/{camera_id}", response_model=CameraConfig)
def get_camera(camera_id: str):
    """获取指定摄像头"""
    if camera_id not in cameras:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="摄像头不存在")
    return cameras[camera_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
