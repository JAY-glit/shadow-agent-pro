"""
sockets.py — Flask-SocketIO wiring for real-time dashboard updates.

Three event types are broadcast:
  - "scan_event"     fired on every scan request (even safe ones) so the
                      dashboard can show a live activity ticker
  - "new_threat"      fired when a scan resolves to suspicious/malicious
  - "threat_updated"  fired when the Celery deep-scan task refines an
                      existing threat's verdict/confidence after the fact
  - "stats_update"    periodic aggregate refresh
"""

from flask_socketio import SocketIO

socketio = SocketIO(cors_allowed_origins="*", async_mode="threading", message_queue=None)


def init_sockets(app):
    import os

    redis_url = os.environ.get("REDIS_URL")
    # Use Redis as the Socket.IO message queue when available so events
    # broadcast from the Celery worker process reach dashboard clients
    # connected to the Flask process (they're separate processes).
    socketio.init_app(app, message_queue=redis_url)

    @socketio.on("connect")
    def handle_connect():
        socketio.emit("connected", {"message": "Live threat feed connected"})

    return socketio


def broadcast_scan_event(url: str, verdict: str, source: str = "url"):
    socketio.emit("scan_event", {"url": url, "verdict": verdict, "source": source})


def broadcast_threat(threat_dict: dict):
    socketio.emit("new_threat", threat_dict)


def broadcast_threat_update(threat_dict: dict):
    socketio.emit("threat_updated", threat_dict)


def broadcast_stats(stats_dict: dict):
    socketio.emit("stats_update", stats_dict)


def broadcast_metrics(metrics_dict: dict):
    socketio.emit("metrics_update", metrics_dict)
