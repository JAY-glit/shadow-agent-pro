from flask import Blueprint, jsonify

import metrics
from auth import require_auth

metrics_bp = Blueprint("metrics", __name__, url_prefix="/api")


@metrics_bp.route("/metrics", methods=["GET"])
@require_auth
def get_metrics():
    return jsonify(metrics.get_snapshot())
