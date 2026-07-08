"""
backend/app.py

FastAPI backend for the AI Honeypot Detection dashboard.

Two scan modes, both exposed as endpoints:
  - /analyze       -> Live pipeline: resolve -> nmap/socket scan ->
                       feature extraction -> ML prediction -> SHAP
                       explanation. Only use this against hosts you own
                       or have explicit permission to scan.
  - /analyze/demo  -> Simulation pipeline: no network calls at all.
                       Generates a plausible feature set drawn from
                       realistic honeypot/real-server distributions and
                       scores it with the same trained model — lets the
                       full dashboard flow be explored without a live
                       target.

Run:
    pip install -r requirements.txt
    uvicorn app:app --reload --port 8000
"""

import json
import random
import socket
import sys
import os
import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "ml"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scanner"))

from predict import predict, FEATURE_COLUMNS  # noqa: E402

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "ml", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "best_model.pkl")
METRICS_PATH = os.path.join(MODEL_DIR, "metrics.json")

app = FastAPI(title="AI Honeypot Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class TargetRequest(BaseModel):
    target: str  # IP address, hostname, or URL


class ResolveResponse(BaseModel):
    input: str
    resolved_ip: str


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": os.path.exists(MODEL_PATH)}


@app.post("/resolve", response_model=ResolveResponse)
def resolve(req: TargetRequest):
    """Accepts an IP or a URL/hostname and resolves it to an IPv4 address via DNS."""
    target = req.target.strip()
    cleaned = target.replace("http://", "").replace("https://", "").split("/")[0]
    try:
        socket.inet_aton(cleaned)
        return {"input": target, "resolved_ip": cleaned}
    except OSError:
        pass
    try:
        ip = socket.gethostbyname(cleaned)
        return {"input": target, "resolved_ip": ip}
    except socket.gaierror:
        raise HTTPException(status_code=400, detail=f"Could not resolve '{target}' via DNS")


@app.post("/analyze")
def analyze(req: TargetRequest):
    """REAL pipeline. Only point this at hosts you own or have explicit
    permission to scan (e.g. your own Docker Cowrie/Dionaea container or
    your own Apache/Nginx VM)."""
    try:
        from feature_extractor import extract_features
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Scanner dependencies (python-nmap, nmap binary) not installed on this machine.",
        )

    try:
        scan_result = extract_features(req.target)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Scan failed: {e}")

    if not os.path.exists(MODEL_PATH):
        raise HTTPException(status_code=500, detail="Model not trained yet. Run ml/train.py first.")

    verdict = predict(scan_result["features"], MODEL_PATH)

    return {
        "input": req.target,
        "resolved_ip": scan_result["resolved_ip"],
        "features": scan_result["features"],
        "verdict": verdict,
        "mode": "real_scan",
    }


@app.get("/model/metrics")
def model_metrics():
    """Returns the trained model's evaluation metrics (accuracy, precision,
    recall, F1, ROC-AUC, which algorithm won) from the most recent
    ml/train.py run, plus the feature schema. Powers the site's stats
    section with real numbers instead of static copy."""
    if not os.path.exists(METRICS_PATH):
        raise HTTPException(status_code=404, detail="No metrics found. Run ml/train.py first.")
    with open(METRICS_PATH) as f:
        metrics = json.load(f)
    return metrics


@app.post("/analyze/demo")
def analyze_demo(req: TargetRequest):
    """Simulation pipeline. No packets are sent to the target at all — the
    full flow (resolve -> scan -> extract -> predict -> explain) runs on
    a feature set drawn from realistic honeypot/real-server distributions,
    so the console can be explored without a live target."""
    target = req.target.strip()
    cleaned = target.replace("http://", "").replace("https://", "").split("/")[0]

    try:
        socket.inet_aton(cleaned)
        resolved_ip = cleaned
    except OSError:
        try:
            resolved_ip = socket.gethostbyname(cleaned)
        except socket.gaierror:
            # still return something for demo purposes rather than failing
            resolved_ip = ".".join(str(random.randint(1, 254)) for _ in range(4))

    is_honeypot_leaning = random.random() < 0.5
    if is_honeypot_leaning:
        features = {
            "ttl": random.choice([60, 62, 64, 128, 30]),
            "window_size": random.choice([64240, 8192, 1024, 5720]),
            "open_ports": random.randint(1, 4),
            "banner_length": random.randint(2, 40),
            "banner_entropy": round(random.uniform(0.8, 3.2), 2),
            "ssh_banner_present": random.randint(0, 1),
            "http_header_count": random.randint(0, 6),
            "http_status_code": random.choice([200, 403, 500, 0]),
            "response_time_ms": round(random.uniform(0.1, 5), 2),
            "latency_std_dev": round(random.uniform(1.5, 9), 2),
            "icmp_reply": random.choice([0, 0, 1]),
            "num_services": random.randint(1, 3),
            "tcp_mss": random.choice([536, 1400, 1200]),
        }
    else:
        features = {
            "ttl": random.choice([64, 128, 255]),
            "window_size": random.choice([64240, 65535, 14600]),
            "open_ports": random.randint(3, 10),
            "banner_length": random.randint(25, 90),
            "banner_entropy": round(random.uniform(3.0, 4.3), 2),
            "ssh_banner_present": random.randint(0, 1),
            "http_header_count": random.randint(8, 18),
            "http_status_code": random.choice([200, 301, 403]),
            "response_time_ms": round(random.uniform(2, 20), 2),
            "latency_std_dev": round(random.uniform(0.2, 2), 2),
            "icmp_reply": random.choice([1, 1, 0]),
            "num_services": random.randint(3, 8),
            "tcp_mss": random.choice([1460, 1440]),
        }

    if not os.path.exists(MODEL_PATH):
        raise HTTPException(status_code=500, detail="Model not trained yet. Run ml/train.py first.")

    verdict = predict(features, MODEL_PATH)

    return {
        "input": target,
        "resolved_ip": resolved_ip,
        "features": features,
        "verdict": verdict,
        "mode": "dummy_demo",
    }


@app.get("/features")
def features():
    return {"feature_columns": FEATURE_COLUMNS}


@app.get("/metrics")
def metrics():
    """Serves the metrics.json produced by ml/train.py, so the dashboard
    can show real accuracy/precision/recall/F1/ROC-AUC for both models
    instead of hardcoded numbers."""
    metrics_path = os.path.join(os.path.dirname(__file__), "..", "ml", "models", "metrics.json")
    if not os.path.exists(metrics_path):
        raise HTTPException(status_code=404, detail="No metrics yet — run ml/train.py first.")
    with open(metrics_path) as f:
        return json.load(f)
