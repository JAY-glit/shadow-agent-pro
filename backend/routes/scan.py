import time

from flask import Blueprint, request, jsonify
import tldextract

from models.database import db, Threat, ScanLog
from ml.predict import classifier
from utils.cache import get_cached_scan, set_cached_scan, REDIS_AVAILABLE
from utils.typosquatting import check_typosquatting
from auth import require_auth
from sockets import broadcast_threat, broadcast_scan_event, broadcast_metrics
import metrics

scan_bp = Blueprint("scan", __name__, url_prefix="/api/scan")


@scan_bp.route("/url", methods=["POST"])
@require_auth
def scan_url():
    """Fast path: returns a verdict in well under a second using only local
    signals (Random Forest on lexical/SSL-handshake-free features +
    typosquat check). A Celery task is queued in the background to run the
    slower WHOIS/SSL/VirusTotal/Safe-Browsing checks and refine the verdict
    a moment later via the 'threat_updated' WebSocket event — the dashboard
    and extension both update in place without a second round-trip."""
    payload = request.get_json(silent=True) or {}
    url = payload.get("url", "").strip()
    if not url:
        return jsonify({"error": "Missing 'url' in request body"}), 400

    start = time.time()

    cached = get_cached_scan(url)
    if cached:
        cached["cached"] = True
        cached["latency_ms"] = int((time.time() - start) * 1000)
        broadcast_scan_event(url, cached["verdict"])
        metrics.record_scan(cached["latency_ms"], cached["verdict"])
        broadcast_metrics(metrics.get_snapshot())
        return jsonify(cached)

    result = classifier.predict(url)

    typo = check_typosquatting(url)
    if typo["is_typosquat"]:
        result["confidence"] = max(result["confidence"], 0.85)
        result["reasons"].insert(
            0, f"Looks like a typosquat of {typo['closest_brand']} (edit distance {typo['distance']})"
        )
        result["verdict"] = "malicious" if result["confidence"] >= classifier.threshold else "suspicious"

    latency_ms = int((time.time() - start) * 1000)
    domain = tldextract.extract(url).registered_domain

    threat = Threat(
        url=url,
        domain=domain,
        verdict=result["verdict"],
        confidence=result["confidence"],
        char_ngram_score=result.get("char_ngram_score"),
        reasons=result["reasons"],
    )
    db.session.add(threat)
    db.session.add(
        ScanLog(url=url, scan_type="url", result_summary=result["verdict"], latency_ms=latency_ms)
    )
    db.session.commit()

    response = {
        "verdict": result["verdict"],
        "confidence": result["confidence"],
        "reasons": result["reasons"],
        "char_ngram_score": result.get("char_ngram_score"),
        "latency_ms": latency_ms,
        "cached": False,
        "deep_scan_pending": True,
        "threat_id": threat.id,
    }

    set_cached_scan(url, response)
    broadcast_scan_event(url, result["verdict"])
    metrics.record_scan(latency_ms, result["verdict"])
    broadcast_metrics(metrics.get_snapshot())

    if result["verdict"] != "safe":
        broadcast_threat(threat.to_dict())

    # Queue the slow, network-bound deep analysis — never blocks this request.
    # Pre-check REDIS_AVAILABLE (a cheap 1s-timeout ping done once at import
    # time in utils/cache.py) rather than calling .delay() blind — without
    # this, a down Redis broker makes Celery/Kombu retry the connection
    # with backoff for 30-45+ seconds before finally giving up, which
    # would silently turn every "fast path" scan into a very slow one.
    if REDIS_AVAILABLE:
        try:
            from tasks import deep_scan_task

            deep_scan_task.delay(threat.id, url)
        except Exception:
            response["deep_scan_pending"] = False
    else:
        response["deep_scan_pending"] = False

    return jsonify(response)


@scan_bp.route("/content", methods=["POST"])
@require_auth
def scan_content():
    """Receives DOM indicators flagged by the extension's content-script,
    optionally re-verifies server-side, and logs the result."""
    payload = request.get_json(silent=True) or {}
    url = payload.get("url", "")
    indicators = payload.get("indicators", {})

    if not url:
        return jsonify({"error": "Missing 'url'"}), 400

    risk_signals = 0
    if indicators.get("credentialForms"):
        risk_signals += sum(1 for f in indicators["credentialForms"] if f.get("crossOrigin"))
    if indicators.get("hiddenIframes"):
        risk_signals += len(indicators["hiddenIframes"])
    if indicators.get("brandImpersonation"):
        risk_signals += len(indicators["brandImpersonation"]) * 2
    if indicators.get("urgencyLanguage"):
        risk_signals += len(indicators["urgencyLanguage"])

    verdict = "malicious" if risk_signals >= 3 else "suspicious" if risk_signals >= 1 else "safe"
    domain = tldextract.extract(url).registered_domain

    if verdict != "safe":
        threat = Threat(
            url=url,
            domain=domain,
            verdict=verdict,
            confidence=min(0.5 + risk_signals * 0.1, 0.99),
            reasons=[f"DOM signal: {k}" for k, v in indicators.items() if v],
        )
        db.session.add(threat)
        db.session.add(ScanLog(url=url, scan_type="content", result_summary=verdict))
        db.session.commit()
        broadcast_threat(threat.to_dict())
    else:
        db.session.add(ScanLog(url=url, scan_type="content", result_summary=verdict))
        db.session.commit()

    broadcast_scan_event(url, verdict, source="content")
    return jsonify({"verdict": verdict, "risk_signals": risk_signals})
