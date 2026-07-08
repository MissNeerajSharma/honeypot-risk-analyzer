"""
predict.py

Loads the trained model and scores a single feature dict, with a real
per-prediction SHAP explanation (Phase 2 — this replaces the Phase 1
stand-in that just showed the model's overall top feature importances).

Used directly by backend/app.py, and also runnable standalone:

    python predict.py --model models/best_model.pkl \
        --features '{"ttl":64,"window_size":64240,"open_ports":5,...}'
"""

import argparse
import json

import joblib
import numpy as np
import pandas as pd
import shap

FEATURE_COLUMNS = [
    "ttl", "window_size", "open_ports", "banner_length", "banner_entropy",
    "ssh_banner_present", "http_header_count", "http_status_code",
    "response_time_ms", "latency_std_dev", "icmp_reply", "num_services",
    "tcp_mss",
]

FEATURE_LABELS = {
    "ttl": "TTL",
    "window_size": "TCP window size",
    "open_ports": "open port count",
    "banner_length": "banner length",
    "banner_entropy": "banner randomness (entropy)",
    "ssh_banner_present": "SSH banner presence",
    "http_header_count": "HTTP header count",
    "http_status_code": "HTTP status code",
    "response_time_ms": "response time",
    "latency_std_dev": "response timing jitter",
    "icmp_reply": "ICMP (ping) reply",
    "num_services": "number of live services",
    "tcp_mss": "TCP MSS",
}

_model_cache = {}
_explainer_cache = {}


def load_model(path: str):
    if path not in _model_cache:
        _model_cache[path] = joblib.load(path)
    return _model_cache[path]


def load_explainer(model, model_path: str):
    if model_path not in _explainer_cache:
        _explainer_cache[model_path] = shap.TreeExplainer(model)
    return _explainer_cache[model_path]


def _honeypot_shap_contributions(explainer, row: pd.DataFrame) -> dict:
    """Returns {feature_name: shap_value}, where a positive value means
    that feature pushed the prediction toward "honeypot" and a negative
    value pushed it toward "real server".

    Different model types return different shapes from shap_values():
      - RandomForestClassifier: shape (1, n_features, n_classes) — one
        set of contributions per class. We take the honeypot (class 1)
        slice.
      - XGBClassifier (binary): shape (1, n_features) — a single set of
        contributions already relative to the positive class.
    This handles both without assuming which model is loaded.
    """
    raw = explainer.shap_values(row)
    arr = np.array(raw)

    if arr.ndim == 3:
        # (n_samples, n_features, n_classes) -> take class 1 (honeypot)
        contributions = arr[0, :, 1]
    elif arr.ndim == 2:
        # (n_samples, n_features) -> already relative to the positive class
        contributions = arr[0]
    else:
        raise ValueError(f"Unexpected SHAP output shape: {arr.shape}")

    return dict(zip(FEATURE_COLUMNS, contributions.tolist()))


def predict(features: dict, model_path: str = "models/best_model.pkl") -> dict:
    model = load_model(model_path)
    row = pd.DataFrame([{col: features.get(col, 0) for col in FEATURE_COLUMNS}])

    pred = int(model.predict(row)[0])
    proba = model.predict_proba(row)[0]
    honeypot_confidence = float(proba[1])
    real_confidence = float(proba[0])

    explainer = load_explainer(model, model_path)
    contributions = _honeypot_shap_contributions(explainer, row)

    # Rank by magnitude of contribution (how much it moved the prediction),
    # not just raw feature value — this is the actual point of SHAP over
    # the Phase 1 global-importance stand-in: it's specific to *this* scan.
    ranked = sorted(contributions.items(), key=lambda kv: abs(kv[1]), reverse=True)

    top_features = []
    for name, value in ranked[:5]:
        top_features.append({
            "feature": name,
            "label": FEATURE_LABELS.get(name, name),
            "value": features.get(name),
            "shap_contribution": round(value, 4),
            "pushes_toward": "honeypot" if value > 0 else "real_server",
        })

    return {
        "prediction": "honeypot" if pred == 1 else "real_server",
        "is_honeypot": bool(pred),
        "honeypot_confidence": round(honeypot_confidence, 4),
        "real_server_confidence": round(real_confidence, 4),
        "top_contributing_features": [f["feature"] for f in top_features],  # kept for backward compatibility
        "explanation": top_features,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Score a feature set against the trained model")
    parser.add_argument("--model", default="models/best_model.pkl")
    parser.add_argument("--features", required=True, help="JSON string of feature values")
    args = parser.parse_args()

    features = json.loads(args.features)
    result = predict(features, args.model)
    print(json.dumps(result, indent=2))
