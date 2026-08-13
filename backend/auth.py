"""
auth.py — lightweight JWT issuing + verification so the extension and
dashboard authenticate to the API instead of leaving every endpoint public.
Each extension install and dashboard session gets a signed token on first
contact; subsequent requests carry it in the Authorization header.
"""

from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import request, jsonify, current_app

TOKEN_TTL_HOURS = 24


def issue_token(client_id: str) -> str:
    payload = {
        "sub": client_id,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_TTL_HOURS),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def verify_token(token: str):
    try:
        return jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def require_auth(f):
    """Decorator for routes that must present a valid Bearer token.
    Kept opt-in per-route (rather than global) so /api/health and the
    token-issuing endpoint itself stay reachable without a token."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify({"error": "Missing or malformed Authorization header"}), 401

        token = header.split(" ", 1)[1]
        payload = verify_token(token)
        if payload is None:
            return jsonify({"error": "Invalid or expired token"}), 401

        request.client_id = payload["sub"]
        return f(*args, **kwargs)

    return wrapper
