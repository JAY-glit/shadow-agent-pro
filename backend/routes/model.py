"""
model.py — exposes metadata about the currently loaded model and a
lightweight drift signal: it compares the malicious-verdict rate over the
last N scans against a stored training-time baseline. A material jump
suggests either a real attack wave or the model no longer matching the
current threat landscape (both worth flagging for retraining).
"""

import json
from pathlib import Path

from flask import Blueprint, jsonify
from sqlalchemy import func

from models.database import db, Threat
from auth import require_auth

model_bp = Blueprint("model", __name__, url_prefix="/api/model")

METADATA_PATH = Path(__file__).parent.parent / "ml" / "artifacts" / "model_metadata.json"
DRIFT_WINDOW = 200  # number of most-recent scans to evaluate
DRIFT_ALERT_THRESHOLD = 0.15  # absolute change in malicious rate that triggers a flag


def _load_metadata() -> dict:
    if not METADATA_PATH.exists():
        return {
            "version": "unset",
            "trained_at": None,
            "baseline_malicious_rate": None,
            "metrics": {},
        }
    return json.loads(METADATA_PATH.read_text())


@model_bp.route("/version", methods=["GET"])
@require_auth
def model_version():
    return jsonify(_load_metadata())


@model_bp.route("/drift", methods=["GET"])
@require_auth
def model_drift():
    meta = _load_metadata()
    baseline = meta.get("baseline_malicious_rate")

    recent = (
        Threat.query.order_by(Threat.detected_at.desc()).limit(DRIFT_WINDOW).all()
    )
    if not recent:
        return jsonify({"status": "no_data"})

    current_rate = sum(1 for t in recent if t.verdict == "malicious") / len(recent)

    if baseline is None:
        return jsonify(
            {
                "status": "no_baseline",
                "current_malicious_rate": round(current_rate, 4),
                "sample_size": len(recent),
                "message": "No training-time baseline recorded in model_metadata.json yet.",
            }
        )

    delta = current_rate - baseline
    drifted = abs(delta) >= DRIFT_ALERT_THRESHOLD

    return jsonify(
        {
            "status": "drift_detected" if drifted else "stable",
            "baseline_malicious_rate": baseline,
            "current_malicious_rate": round(current_rate, 4),
            "delta": round(delta, 4),
            "sample_size": len(recent),
            "recommendation": (
                "Consider retraining on recent labeled data."
                if drifted
                else "No retraining needed based on current signal."
            ),
        }
    )


@model_bp.route("/feature-importance", methods=["GET"])
@require_auth
def feature_importance():
    """Returns the Random Forest's feature_importances_, ranked. This is a
    coarser, cheaper form of transparency than the per-request SHAP
    explanation in ml/predict.py — SHAP explains one prediction, this
    explains the model's overall behavior across all of training, useful
    for the Analytics dashboard tab and for sanity-checking during
    development that engineered features are actually pulling their
    weight (see ml-training/notebooks/eda.ipynb for the same check done
    interactively against a specific dataset sample)."""
    from ml.predict import classifier
    from ml.feature_extraction import FEATURE_ORDER

    if classifier.model is None:
        return jsonify({"status": "model_not_loaded", "features": []})

    try:
        importances = classifier.model.feature_importances_
    except AttributeError:
        return jsonify({"status": "unavailable", "features": []})

    ranked = sorted(zip(FEATURE_ORDER, importances), key=lambda x: x[1], reverse=True)

    return jsonify(
        {
            "status": "ok",
            "features": [{"name": name, "importance": round(float(score), 4)} for name, score in ranked],
        }
    )
