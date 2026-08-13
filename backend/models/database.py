from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utcnow():
    return datetime.now(timezone.utc)


class Threat(db.Model):
    __tablename__ = "threats"

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(2048), nullable=False, index=True)
    domain = db.Column(db.String(255), index=True)
    verdict = db.Column(db.String(20), nullable=False)  # safe | suspicious | malicious
    confidence = db.Column(db.Float, nullable=False)
    char_ngram_score = db.Column(db.Float, nullable=True)  # second-opinion model's independent score, for transparency
    reasons = db.Column(db.JSON, default=list)
    detected_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "url": self.url,
            "domain": self.domain,
            "verdict": self.verdict,
            "confidence": self.confidence,
            "char_ngram_score": self.char_ngram_score,
            "reasons": self.reasons,
            "detected_at": self.detected_at.isoformat(),
        }


class ScanLog(db.Model):
    __tablename__ = "scan_logs"

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(2048), nullable=False)
    scan_type = db.Column(db.String(20))  # url | content
    result_summary = db.Column(db.String(255))
    latency_ms = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=utcnow)


class Whitelist(db.Model):
    __tablename__ = "whitelist"

    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(255), unique=True, nullable=False)
    added_at = db.Column(db.DateTime, default=utcnow)


class Statistics(db.Model):
    __tablename__ = "statistics"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False)
    total_scans = db.Column(db.Integer, default=0)
    malicious_count = db.Column(db.Integer, default=0)
    suspicious_count = db.Column(db.Integer, default=0)
    safe_count = db.Column(db.Integer, default=0)


class Feedback(db.Model):
    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(2048), nullable=False)
    note = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=utcnow)
