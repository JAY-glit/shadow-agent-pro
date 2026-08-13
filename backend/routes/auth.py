import uuid

from flask import Blueprint, request, jsonify

from auth import issue_token

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/token", methods=["POST"])
def get_token():
    """Issues a client token. In production this would validate an
    extension install ID or dashboard login; for the project scope, any
    caller gets a scoped token identified by a generated/given client_id."""
    payload = request.get_json(silent=True) or {}
    client_id = payload.get("client_id") or str(uuid.uuid4())

    token = issue_token(client_id)
    return jsonify({"token": token, "client_id": client_id, "expires_in_hours": 24})
