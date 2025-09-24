import os
import uuid
from typing import Optional, List

import httpx
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
import shutil
from pydantic import BaseModel
from ultralytics import YOLO
import tempfile


BACKEND_BASE = os.getenv("BACKEND_BASE", "http://backend:8080")

app = FastAPI(title="Vision Service", version="0.2.0")


class VisionEvent(BaseModel):
    timestamp: Optional[str] = None
    trackId: str
    bbox: List[int]
    action: Optional[str] = None
    riskScore: Optional[float] = None


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
    return emit(e)  # type: ignore[arg-type]


# Lazy-load model to speed up container cold start path until first inference
_model: Optional[YOLO] = None


def get_model() -> YOLO:
    global _model
    if _model is None:
        weights = os.getenv("YOLO_WEIGHTS", "yolov8n.pt")
        _model = YOLO(weights)
    return _model


@app.post("/infer")
def infer(
    source_url: Optional[str] = Form(default=None),
    track_id: Optional[str] = Form(default=None),
    file: Optional[UploadFile] = File(default=None),
):
    model = get_model()

    if not source_url and not file:
        return {"error": "provide source_url or file"}

    input_path: Optional[str] = None
    temp_file = None
    try:
        if source_url:
            # 下载 URL 到临时文件，避免容器内 OpenCV 对外网/SSL 的兼容问题
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
            # persist upload to a temp file for YOLO
            suffix = os.path.splitext(file.filename or "upload.jpg")[1]
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp_file.write(file.file.read())
            temp_file.flush()
            temp_file.close()
            input_path = temp_file.name

        results = model.predict(source=input_path, imgsz=640, conf=0.25, verbose=False)
        if not results:
            return {"detections": []}

        # choose first frame result
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

        # pick a primary detection, prefer person class if present (COCO person=0)
        primary = None
        persons = [d for d in detections if d.get("classId") == 0]
        primary = max(persons or detections, key=lambda d: d.get("conf", 0.0), default=None)

        if primary is None:
            return {"detections": detections, "emitted": False}

        # 将最近输入保存为最近帧，供前端缩略图使用
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

