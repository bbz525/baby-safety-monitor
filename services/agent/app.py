import os
import json
from typing import Optional

import httpx
import requests
from fastapi import FastAPI, BackgroundTasks
from sseclient import SSEClient


BACKEND_BASE = os.getenv("BACKEND_BASE", "http://backend:8080")
EVENTS_BASE = os.getenv("EVENTS_BASE", f"{BACKEND_BASE}/api/events")

RISK_THRESHOLD = float(os.getenv("RISK_THRESHOLD", "0.7"))
app = FastAPI(title="Agent Service", version="0.2.0")


@app.get("/health")
def health():
    return {"status": "ok", "backend": BACKEND_BASE}


def _report(level: str = "warn", reason: str = "stub", trackId: Optional[str] = None, zoneId: Optional[int] = None, details: Optional[dict] = None):
    payload = {
        "timestamp": None,
        "trackId": trackId,
        "zoneId": zoneId,
        "level": level,
        "reason": reason,
        "detailsJson": json.dumps(details or {}),
    }
    url = f"{BACKEND_BASE}/api/agent/insights"
    with httpx.Client(timeout=5.0) as client:
        r = client.post(url, json=payload)
        r.raise_for_status()
    return {"sent": True}


@app.post("/report")
def report(level: str = "warn", reason: str = "stub", trackId: Optional[str] = None):
    return _report(level=level, reason=reason, trackId=trackId)


def _subscribe_and_infer_rules():
    stream_url = f"{EVENTS_BASE}/stream"
    resp = requests.get(stream_url, stream=True, headers={"Accept": "text/event-stream"}, timeout=30)
    client = SSEClient(resp)
    for event in client.events():
        try:
            data = json.loads(event.data)
        except Exception:
            continue
        # Heuristic: treat objects with bbox as vision events
        if all(k in data for k in ("x", "y", "w", "h")):
            risk = float(data.get("riskScore") or 0.0)
            if risk >= RISK_THRESHOLD:
                _report(
                    level="warn" if risk < 0.9 else "critical",
                    reason=f"high risk score {risk:.2f}",
                    trackId=data.get("trackId"),
                    zoneId=None,
                    details={
                        "source": "rule:riskScore",
                        "eventId": data.get("id"),
                        "imageUrl": os.getenv("VISION_BASE", "http://vision:8001") + "/last.jpg",
                    },
                )


@app.post("/start")
def start(background: BackgroundTasks):
    background.add_task(_subscribe_and_infer_rules)
    return {"started": True, "threshold": RISK_THRESHOLD}


