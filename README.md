<div align="center">
 ___ _  _   _   ___   _____      __    _   ___ ___ _  _ _____   ___ ___  ___
/ __| || | /_\ |   \ / _ \ \    / /   /_\ / __| __| \| |_   _| | _ \ _ \/ _ \
\__ \ __ |/ _ \| |) | (_) \ \/\/ /   / _ \ (_ | _|| .` | | |   |  _/   / (_) |
|___/_||_/_/ \_\___/ \___/ \_/\_/   /_/ \_\___|___|_|\_| |_|   |_| |_|_\\___/

real-time ML-powered malware & phishing detection chrome extension · flask api · react dashboard

Show Image Show Image Show Image

→ github.com/JAY-glit/shadow-agent-pro

</div> <br>
┌─ SESSION LOG ──────────────────────────────────────────────────────────────┐
bash
$ curl -X POST localhost:5000/api/scan/url -d '{"url":"http://paypa1-secure-login.tk/verify-account"}'
json
{
  "verdict": "malicious",
  "confidence": 0.7537,
  "char_ngram_score": 0.3835,
  "reasons": ["No valid SSL certificate"],
  "latency_ms": 3597
}
bash
$ curl -X POST localhost:5000/api/scan/url -d '{"url":"https://www.google.com"}'
json
{
  "verdict": "safe",
  "confidence": 0.02,
  "reasons": ["google.com is a recognized, well-known legitimate domain"]
}
└──────────────────────────────────────────────────────────────────────────┘

Two live scans, two verdicts, both correct — one caught by engineered features spotting a missing SSL cert, one trusted instantly via an allowlist instead of getting fooled by ML text patterns. That divergence is the whole design philosophy of this project: don't trust one signal.

<br>
SYSTEM MAP
Background (Celery)
Flask API
Client
Browser
POST scan/url
POST scan/url
queues
threat_updated event
WebSocket push
cache
sync blocklist every 5 min
Chrome ExtensionMV3 service worker
React DashboardVite + Socket.IO
/api/scan/urlfast heuristic verdict
Random Forest25+ engineered features
Char n-gram modelindependent secondopinion
JWT auth
deep_scan_task
WHOIS domain age
SSL cert check
VirusTotal
Safe Browsing
SQLitethreats, scan_logs
Rediscache + broker + socketqueue

> the fast path never touches the network beyond the request itself. everything slow happens in the background and pushes back live.

<br>
INCIDENT LOG

Two real bugs, found through real testing, documented instead of hidden.

┌─ INCIDENT #001 ────────────────────────────────────────────────────────────
│ SEVERITY: model bias
│ STATUS:   resolved
├─────────────────────────────────────────────────────────────────────────
│ https://www.google.com scored 93% malicious on the character n-gram
│ model. Root cause: in the training sample, malicious URLs containing
│ "goog" (brand-impersonation attempts) outnumbered legitimate Google
│ URLs 2:1 — attackers impersonate popular brands so heavily that a
│ naive text model learns to distrust the brand names themselves.
│
│ FIX: exact-match allowlist (utils/allowlist.py), verified with
│ regression tests to confirm it can't be defeated by a phishing domain
│ merely *containing* a brand name.
└─────────────────────────────────────────────────────────────────────────
┌─ INCIDENT #002 ────────────────────────────────────────────────────────────
│ SEVERITY: suspiciously good result
│ STATUS:   investigated, explained
├─────────────────────────────────────────────────────────────────────────
│ A training run on live URLhaus + Tranco data hit 100.00% accuracy.
│ Real classifiers don't do that — so it was investigated, not reported
│ blindly. Root cause: URLhaus's malicious set is mostly raw IP-address
│ malware links; Tranco's benign set is exclusively clean top-domain
│ names. Lexically almost trivially separable.
│
│ VALIDATION: stress-tested against a harder, hand-built typosquat with
│ no IP address. Result — RF: 95.3% malicious, char-ngram: 38.4%
│ malicious, ensemble: 75.4% malicious, correct. The two models
│ disagreed for a real reason, and the stronger signal won.
└─────────────────────────────────────────────────────────────────────────
<br>
MODULES
detection/
├── random_forest ──── 25+ lexical, domain, SSL features · RandomizedSearchCV-tuned
├── char_ngram ──────── TF-IDF + LogisticRegression, raw text, no manual features
├── shap ────────────── per-prediction explainability, 2s hard timeout
├── typosquat ───────── Levenshtein distance vs. curated brand list
└── allowlist ───────── exact-match, un-defeatable by substring tricks

realtime/
├── async_scan ──────── heuristic verdict <1s → background deep-scan → push
├── websocket ───────── live threat feed, metrics, activity ticker
├── blocklist_sync ──── extension pulls confirmed-malicious domains every 5m
└── command_palette ─── ⌘K to navigate or scan without touching the mouse

ops/
├── status ──────────── one endpoint, every subsystem's health
├── metrics ─────────── live req/min, p50/p95 latency, scan volume
├── drift ───────────── current malicious-rate vs. training baseline
└── tests ───────────── 48 passing, zero network dependency, real CI
<br> <div align="center">
$ git clone https://github.com/JAY-glit/shadow-agent-pro.git

→ full repo, docs, and code

</div>
