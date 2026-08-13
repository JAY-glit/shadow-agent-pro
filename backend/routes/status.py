"""
status.py — a single endpoint that reports the health of every subsystem
this app depends on (DB, Redis/cache, model artifacts, external threat
intel keys). This is the kind of thing a real SaaS status page is built
on top of, and it's genuinely useful during your demo/viva: instead of
guessing why a scan looks off, you can hit one endpoint and see exactly
what's connected and what isn't.
"""

from flask import Blueprint, jsonify

from models.database import db, Threat
from ml.predict import classifier
from ml.char_ngram_model import char_ngram_classifier
from utils.cache import REDIS_AVAILABLE
from auth import require_auth

status_bp = Blueprint("status", __name__, url_prefix="/api")


@status_bp.route("/status", methods=["GET"])
@require_auth
def system_status():
    checks = {}

    # Database
    try:
        db.session.query(Threat.id).limit(1).all()
        checks["database"] = {"status": "ok"}
    except Exception as e:
        checks["database"] = {"status": "error", "detail": str(e)}

    # Redis / cache + async pipeline
    checks["redis"] = {
        "status": "ok" if REDIS_AVAILABLE else "unavailable",
        "note": "Caching and async deep-scan are disabled without Redis; "
        "scans still work, just heuristic-only and uncached."
        if not REDIS_AVAILABLE
        else "Caching and async deep-scan active.",
    }

    # ML model
    model_loaded = classifier.model is not None
    checks["ml_model"] = {
        "status": "ok" if model_loaded else "not_loaded",
        "note": "Run ml-training/train.py to produce a model." if not model_loaded else None,
    }

    # Second-opinion char n-gram model
    char_ngram_classifier._ensure_loaded()
    checks["char_ngram_model"] = {
        "status": "ok" if char_ngram_classifier.pipeline is not None else "not_loaded",
        "note": "Optional — ensemble falls back to RF-only scoring without it."
        if char_ngram_classifier.pipeline is None
        else None,
    }

    # External threat intel
    from flask import current_app

    checks["virustotal"] = {
        "status": "ok" if current_app.config.get("VIRUSTOTAL_API_KEY") else "no_key"
    }
    checks["safe_browsing"] = {
        "status": "ok" if current_app.config.get("SAFE_BROWSING_API_KEY") else "no_key"
    }

    critical_ok = checks["database"]["status"] == "ok"
    overall = "healthy" if critical_ok and model_loaded else "degraded" if critical_ok else "unhealthy"

    return jsonify({"overall": overall, "checks": checks})
