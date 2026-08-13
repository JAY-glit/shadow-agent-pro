"""
tasks.py — background jobs run by the Celery worker.

deep_scan_task does the slow work (WHOIS domain age, SSL handshake,
VirusTotal, Safe Browsing, server-side content re-verification) that would
otherwise make a synchronous scan request take 3-8 seconds. The Flask route
returns a fast heuristic-only verdict immediately and this task updates the
Threat row + pushes the refined verdict over the socket when it lands.
"""

from celery_app import celery_app


def _create_app_context():
    """Celery workers run in a separate process, so each task needs its own
    Flask app context to touch the DB / config, built lazily to avoid
    circular imports at module load time."""
    from app import create_app

    app = create_app()
    return app


@celery_app.task(bind=True, max_retries=2)
def deep_scan_task(self, threat_id: int, url: str):
    app = _create_app_context()
    with app.app_context():
        from models.database import db, Threat
        from utils.whois_check import get_domain_age_days
        from utils.ssl_check import check_ssl
        from utils.threat_intel import check_virustotal, check_safe_browsing, fuse_verdict
        from sockets import broadcast_threat_update
        import tldextract
        from urllib.parse import urlparse

        threat = db.session.get(Threat, threat_id)
        if threat is None:
            return {"status": "threat_not_found"}

        domain = tldextract.extract(url).registered_domain
        hostname = urlparse(url).netloc

        try:
            age_days = get_domain_age_days(domain)
        except Exception:
            age_days = -1

        try:
            ssl_info = check_ssl(hostname)
        except Exception:
            ssl_info = {}

        vt_result = check_virustotal(url)
        sb_result = check_safe_browsing(url)

        fused_confidence, intel_reasons = fuse_verdict(threat.confidence, vt_result, sb_result)

        extra_reasons = []
        if age_days != -1 and age_days < 30:
            extra_reasons.append(f"Domain registered {age_days} days ago")
        if ssl_info and not ssl_info.get("valid"):
            extra_reasons.append("No valid SSL certificate on deep inspection")
        if ssl_info.get("self_signed"):
            extra_reasons.append("Self-signed SSL certificate detected")

        threat.confidence = fused_confidence
        threat.reasons = list(dict.fromkeys(intel_reasons + extra_reasons + (threat.reasons or [])))
        if fused_confidence >= 0.6:
            threat.verdict = "malicious"
        elif fused_confidence >= 0.3:
            threat.verdict = "suspicious"

        db.session.commit()
        broadcast_threat_update(threat.to_dict())

        return {"status": "completed", "threat_id": threat_id, "verdict": threat.verdict}


@celery_app.task
def sync_blocklist_task():
    """Periodic job (see celery beat schedule) that could push a refreshed
    malicious-domain list to a shared cache for the extension's blocklist
    sync endpoint. Kept as a lightweight placeholder for the beat schedule."""
    app = _create_app_context()
    with app.app_context():
        from models.database import db, Threat

        malicious_domains = (
            db.session.query(Threat.domain)
            .filter(Threat.verdict == "malicious")
            .distinct()
            .all()
        )
        return {"count": len(malicious_domains)}
