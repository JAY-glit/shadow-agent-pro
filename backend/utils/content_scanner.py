"""content_scanner.py — server-side reinforcement of the content-script's
DOM findings. Optionally re-fetches and parses the page HTML with
BeautifulSoup4 for a second-opinion pass (credential forms, hidden iframes,
obfuscated JS, urgency language)."""

import re

import requests
from bs4 import BeautifulSoup

URGENCY_PHRASES = [
    "verify your account", "act now", "account suspended",
    "confirm your identity", "urgent action required", "unusual activity detected",
]


def analyze_html(html: str, base_url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    credential_forms = []
    for form in soup.find_all("form"):
        if form.find("input", {"type": "password"}):
            action = form.get("action", "")
            credential_forms.append(action)

    hidden_iframes = [
        iframe.get("src", "")
        for iframe in soup.find_all("iframe")
        if "display:none" in (iframe.get("style") or "").replace(" ", "")
        or iframe.get("width") in ("0", "1")
    ]

    scripts_text = " ".join(s.get_text() for s in soup.find_all("script"))
    obfuscation_hits = len(re.findall(r"\beval\(|\bunescape\(|\bfromCharCode\(", scripts_text))

    page_text = soup.get_text(" ").lower()
    urgency_hits = [p for p in URGENCY_PHRASES if p in page_text]

    return {
        "credential_forms": credential_forms,
        "hidden_iframes": hidden_iframes,
        "obfuscated_js_hits": obfuscation_hits,
        "urgency_language": urgency_hits,
        "risk_score": _score(credential_forms, hidden_iframes, obfuscation_hits, urgency_hits),
    }


def fetch_and_analyze(url: str, timeout: float = 5.0) -> dict:
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "ShadowAgentPro/1.0"})
        return analyze_html(resp.text, url)
    except requests.RequestException as e:
        return {"error": str(e)}


def _score(forms, iframes, obf_hits, urgency):
    score = 0.0
    score += 0.4 if forms else 0
    score += 0.2 if iframes else 0
    score += min(obf_hits * 0.1, 0.2)
    score += min(len(urgency) * 0.1, 0.2)
    return round(min(score, 1.0), 2)
