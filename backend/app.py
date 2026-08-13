import os

from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import Config
from models.database import db
from ml.predict import classifier
from sockets import init_sockets
from logging_config import configure_logging


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    configure_logging(app)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    Limiter(get_remote_address, app=app, default_limits=[app.config["RATELIMIT_DEFAULT"]])

    # Register blueprints
    from routes.scan import scan_bp
    from routes.threats import threats_bp
    from routes.stats import stats_bp
    from routes.auth import auth_bp
    from routes.geo import geo_bp
    from routes.model import model_bp
    from routes.status import status_bp
    from routes.metrics import metrics_bp

    app.register_blueprint(scan_bp)
    app.register_blueprint(threats_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(geo_bp)
    app.register_blueprint(model_bp)
    app.register_blueprint(status_bp)
    app.register_blueprint(metrics_bp)

    init_sockets(app)

    with app.app_context():
        db.create_all()
        try:
            classifier.load()
        except FileNotFoundError:
            app.logger.warning(
                "No trained model found at %s — run ml-training/train.py first.",
                app.config["MODEL_PATH"],
            )

    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"})

    @app.route("/", methods=["GET"])
    def index():
        return jsonify(
            {
                "service": "Shadow Agent Pro API",
                "status": "running",
                "docs": "See README.md for the full endpoint list",
                "health": "/api/health",
            }
        )

    vt_active = bool(app.config.get("VIRUSTOTAL_API_KEY"))
    sb_active = bool(app.config.get("SAFE_BROWSING_API_KEY"))
    app.logger.info(
        "Threat intel: VirusTotal=%s, Safe Browsing=%s (set VIRUSTOTAL_API_KEY / "
        "SAFE_BROWSING_API_KEY in backend/.env to enable — see .env.example)",
        "enabled" if vt_active else "disabled (no key)",
        "enabled" if sb_active else "disabled (no key)",
    )

    return app


if __name__ == "__main__":
    app = create_app()
    from sockets import socketio

    socketio.run(app, debug=True, port=5000)
