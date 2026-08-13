"""
celery_app.py — Celery worker configuration. Slow, network-bound checks
(WHOIS, SSL handshake, VirusTotal, Safe Browsing) run here instead of
blocking the Flask request thread, so /api/scan/url can return an instant
heuristic verdict while the deep analysis completes a second or two later
and gets pushed to clients over the WebSocket.
"""

import os
from celery import Celery

REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")

celery_app = Celery(
    "shadow_agent_pro",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_time_limit=20,  # kill any check that hangs past 20s (e.g. slow WHOIS server)
    worker_prefetch_multiplier=4,
    # Fail fast rather than retrying for tens of seconds when the broker is
    # unreachable. Without this, a single .delay() call against a down
    # Redis instance can block the calling Flask request thread for
    # 30-45+ seconds while Kombu retries with exponential backoff — exactly
    # the kind of silent hang this project has already hit with WHOIS and
    # SHAP. routes/scan.py additionally pre-checks Redis reachability
    # before ever calling .delay(), so this is a second line of defense.
    broker_connection_retry_on_startup=False,
    broker_connection_retry=False,
    broker_connection_timeout=2,
)
