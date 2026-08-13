"""
threat_intel.py — cross-checks a URL against external threat intel APIs
(VirusTotal, Google Safe Browsing) to fuse a second opinion with the local
Random Forest verdict. Both calls are optional and fail soft (return
unknown/None) if no API key is configured or the request times out, so the
core pipeline never depends on external uptime.
"""

import base64
import requests

from flask import current_app

VT_URL = "https://www.virustotal.com/api/v3/urls"
SAFE_BROWSING_URL = "https://safebrowsing.googleapis.com/v4/threatMatches:find"


def check_virustotal(url: str, timeout: float = 5.0) -> dict:
    api_key = current_app.config.get("VIRUSTOTAL_API_KEY")
    if not api_key:
        return {"available": False}

    try:
        url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
        resp = requests.get(
            f"{VT_URL}/{url_id}",
            headers={"x-apikey": api_key},
            timeout=timeout,
        )
        if resp.status_code == 404:
            # Not previously scanned by VT — submit it for analysis
            requests.post(VT_URL, headers={"x-apikey": api_key}, data={"url": url}, timeout=timeout)
            return {"available": True, "known": False}

        resp.raise_for_status()
        stats = resp.json()["data"]["attributes"]["last_analysis_stats"]
        malicious_engines = stats.get("malicious", 0) + stats.get("suspicious", 0)
        total_engines = sum(stats.values())

        return {
            "available": True,
            "known": True,
            "malicious_engines": malicious_engines,
            "total_engines": total_engines,
            "flagged": malicious_engines > 0,
        }
    except requests.RequestException:
        return {"available": False, "error": "virustotal_unreachable"}


def check_safe_browsing(url: str, timeout: float = 5.0) -> dict:
    api_key = current_app.config.get("SAFE_BROWSING_API_KEY")
    if not api_key:
        return {"available": False}

    payload = {
        "client": {"clientId": "shadow-agent-pro", "clientVersion": "1.0.0"},
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}],
        },
    }

    try:
        resp = requests.post(
            f"{SAFE_BROWSING_URL}?key={api_key}", json=payload, timeout=timeout
        )
        resp.raise_for_status()
        matches = resp.json().get("matches", [])
        return {
            "available": True,
            "flagged": len(matches) > 0,
            "threat_types": [m.get("threatType") for m in matches],
        }
    except requests.RequestException:
        return {"available": False, "error": "safe_browsing_unreachable"}


def fuse_verdict(local_confidence: float, vt_result: dict, sb_result: dict) -> tuple[float, list[str]]:
    """Blends the local model's confidence with external signals.
    Any confirmed external flag pushes confidence toward 'malicious'
    regardless of the local score, since these are curated ground-truth
    blocklists maintained by dedicated security teams."""
    adjusted = local_confidence
    reasons = []

    if vt_result.get("flagged"):
        adjusted = max(adjusted, 0.9)
        reasons.append(
            f"Flagged by {vt_result['malicious_engines']}/{vt_result['total_engines']} VirusTotal engines"
        )

    if sb_result.get("flagged"):
        adjusted = max(adjusted, 0.95)
        types = ", ".join(sb_result.get("threat_types", []))
        reasons.append(f"Google Safe Browsing match: {types}")

    return round(adjusted, 4), reasons
