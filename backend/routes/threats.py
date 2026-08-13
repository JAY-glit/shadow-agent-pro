from flask import Blueprint, request, jsonify

from models.database import db, Threat
from auth import require_auth

threats_bp = Blueprint("threats", __name__, url_prefix="/api/threats")


@threats_bp.route("", methods=["GET"])
@require_auth
def list_threats():
    limit = min(int(request.args.get("limit", 50)), 500)
    verdict_filter = request.args.get("verdict")

    query = Threat.query
    if verdict_filter:
        query = query.filter_by(verdict=verdict_filter)

    threats = query.order_by(Threat.detected_at.desc()).limit(limit).all()
    return jsonify([t.to_dict() for t in threats])


@threats_bp.route("/domains", methods=["GET"])
@require_auth
def malicious_domains():
    """Distinct confirmed-malicious domains, used by the extension to
    proactively sync a local declarativeNetRequest blocklist so repeat
    offenders are blocked instantly without a live scan round-trip."""
    rows = (
        db.session.query(Threat.domain)
        .filter(Threat.verdict == "malicious", Threat.domain.isnot(None), Threat.domain != "")
        .distinct()
        .all()
    )
    return jsonify({"domains": [r[0] for r in rows]})


@threats_bp.route("/<int:threat_id>", methods=["GET"])
@require_auth
def get_threat(threat_id):
    threat = Threat.query.get_or_404(threat_id)
    return jsonify(threat.to_dict())


@threats_bp.route("/<int:threat_id>", methods=["DELETE"])
@require_auth
def delete_threat(threat_id):
    threat = Threat.query.get_or_404(threat_id)
    db.session.delete(threat)
    db.session.commit()
    return jsonify({"deleted": threat_id})
