import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")  # no-op if the file doesn't exist — fine for local dev without any keys set


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'shadowagent.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MODEL_PATH = BASE_DIR / "ml" / "artifacts" / "random_forest_model.joblib"
    SCALER_PATH = BASE_DIR / "ml" / "artifacts" / "feature_scaler.joblib"

    MALICIOUS_THRESHOLD = 0.6
    DOMAIN_AGE_RISK_DAYS = 30

    VIRUSTOTAL_API_KEY = os.environ.get("VIRUSTOTAL_API_KEY", "")
    SAFE_BROWSING_API_KEY = os.environ.get("SAFE_BROWSING_API_KEY", "")

    RATELIMIT_DEFAULT = "60 per minute"
