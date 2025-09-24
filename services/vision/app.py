import os
import time
from typing import Optional, List

import httpx
from fastapi import FastAPI
from pydantic import BaseModel


BACKEND_BASE = os.getenv("BACKEND_BASE", "http://backend:8080")

app = FastAPI(title="Vision Stub", version="0.1.0")


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


