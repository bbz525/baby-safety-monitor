import os
from typing import Optional

import httpx
from fastapi import FastAPI


BACKEND_BASE = os.getenv("BACKEND_BASE", "http://backend:8080")
EVENTS_BASE = os.getenv("EVENTS_BASE", f"{BACKEND_BASE}/api/events")

app = FastAPI(title="Agent Stub", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok", "backend": BACKEND_BASE}


@app.post("/report")
def report(level: str = "warn", reason: str = "stub", trackId: Optional[str] = None):
    payload = {
        "timestamp": None,
        "trackId": trackId,
        "zoneId": None,
        "level": level,
        "reason": reason,
        "detailsJson": "{}",
    }
    url = f"{BACKEND_BASE}/api/agent/insights"
    with httpx.Client(timeout=5.0) as client:
        r = client.post(url, json=payload)
        r.raise_for_status()
    return {"sent": True}


