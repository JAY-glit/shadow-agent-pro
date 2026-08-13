from datetime import date

from flask import Blueprint, request, jsonify
from sqlalchemy import func

from models.database import db, Threat, Feedback
from auth import require_auth

stats_bp = Blueprint("stats", __name__, url_prefix="/api")


@stats_bp.route("/stats", methods=["GET"])
@require_auth
def get_stats():
    total = db.session.query(func.count(Threat.id)).scalar()
    by_verdict = dict(
        db.session.query(Threat.verdict, func.count(Threat.id)).group_by(Threat.verdict).all()
    )
    top_domains = (
        db.session.query(Threat.domain, func.count(Threat.id).label("count"))
        .filter(Threat.verdict == "malicious")
        .group_by(Threat.domain)
        .order_by(func.count(Threat.id).desc())
        .limit(5)
        .all()
    )

    return jsonify(
        {
            "total_scans": total,
            "safe": by_verdict.get("safe", 0),
            "suspicious": by_verdict.get("suspicious", 0),
            "malicious": by_verdict.get("malicious", 0),
            "top_malicious_domains": [{"domain": d, "count": c} for d, c in top_domains],
        }
    )


@stats_bp.route("/feedback", methods=["POST"])
def submit_feedback():
    payload = request.get_json(silent=True) or {}
    url = payload.get("url", "")
    note = payload.get("note", "user-reported")
    if not url:
        return jsonify({"error": "Missing 'url'"}), 400

    db.session.add(Feedback(url=url, note=note))
    db.session.commit()
    return jsonify({"status": "logged"})
