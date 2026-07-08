"""
train.py

Trains Random Forest and XGBoost on the dataset (synthetic for Phase 1,
your real lab data for Phase 2+), compares them, and saves the best
model to ml/models/best_model.pkl plus a metrics report.

Run:
    python train.py --data ../dataset/dataset.csv --out models/
"""

import argparse
import json
import os

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                              f1_score, roc_auc_score, confusion_matrix,
                              classification_report)
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

FEATURE_COLUMNS = [
    "ttl", "window_size", "open_ports", "banner_length", "banner_entropy",
    "ssh_banner_present", "http_header_count", "http_status_code",
    "response_time_ms", "latency_std_dev", "icmp_reply", "num_services",
    "tcp_mss",
]
LABEL_COLUMN = "is_honeypot"


def evaluate(model, X_test, y_test):
    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)[:, 1]
    return {
        "accuracy": round(accuracy_score(y_test, preds), 4),
        "precision": round(precision_score(y_test, preds), 4),
        "recall": round(recall_score(y_test, preds), 4),
        "f1": round(f1_score(y_test, preds), 4),
        "roc_auc": round(roc_auc_score(y_test, probs), 4),
        "confusion_matrix": confusion_matrix(y_test, preds).tolist(),
    }


def main():
    parser = argparse.ArgumentParser(description="Train honeypot-detection models")
    parser.add_argument("--data", default="../dataset/dataset.csv")
    parser.add_argument("--out", default="models")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    df = pd.read_csv(args.data)
    X = df[FEATURE_COLUMNS]
    y = df[LABEL_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=args.seed, stratify=y
    )

    rf = RandomForestClassifier(
        n_estimators=300, max_depth=None, random_state=args.seed,
        class_weight="balanced",
    )
    rf.fit(X_train, y_train)
    rf_metrics = evaluate(rf, X_test, y_test)

    # scale_pos_weight tells XGBoost how much to up-weight the positive
    # class (honeypot=1) relative to its actual frequency in y_train —
    # this is the standard XGBoost equivalent of class_weight="balanced"
    neg, pos = (y_train == 0).sum(), (y_train == 1).sum()
    scale_pos_weight = neg / pos if pos > 0 else 1.0

    xgb = XGBClassifier(
        n_estimators=300, max_depth=6, learning_rate=0.1,
        eval_metric="logloss", random_state=args.seed,
        scale_pos_weight=scale_pos_weight,
    )
    xgb.fit(X_train, y_train)
    xgb_metrics = evaluate(xgb, X_test, y_test)

    print("=== Random Forest ===")
    print(json.dumps(rf_metrics, indent=2))
    print("\n=== XGBoost ===")
    print(json.dumps(xgb_metrics, indent=2))

    # pick best by ROC-AUC (robust to class balance), tie-break on F1
    best_name, best_model, best_metrics = ("random_forest", rf, rf_metrics)
    if (xgb_metrics["roc_auc"], xgb_metrics["f1"]) > (rf_metrics["roc_auc"], rf_metrics["f1"]):
        best_name, best_model, best_metrics = ("xgboost", xgb, xgb_metrics)

    joblib.dump(rf, os.path.join(args.out, "random_forest.pkl"))
    joblib.dump(xgb, os.path.join(args.out, "xgboost.pkl"))
    joblib.dump(best_model, os.path.join(args.out, "best_model.pkl"))

    report = {
        "best_model": best_name,
        "random_forest": rf_metrics,
        "xgboost": xgb_metrics,
        "feature_columns": FEATURE_COLUMNS,
    }
    with open(os.path.join(args.out, "metrics.json"), "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nBest model: {best_name} -> saved to {args.out}/best_model.pkl")
    print(f"Full report: {args.out}/metrics.json")

    # feature importance (RF) for a quick sanity check / early explainability
    importances = sorted(
        zip(FEATURE_COLUMNS, rf.feature_importances_),
        key=lambda x: x[1], reverse=True,
    )
    print("\nRandom Forest feature importances:")
    for name, imp in importances:
        print(f"  {name:<20s} {imp:.4f}")


if __name__ == "__main__":
    main()
