<div align="center">
🛡️ Shadow Agent Pro
Real-time, ML-powered malware & phishing detection

Chrome extension + Flask API + React dashboard — a two-model ML ensemble, an async detection pipeline, live threat intelligence, and a full real-time operations layer.

Show Image Show Image Show Image Show Image

→ View the full repository

</div> <br>
What it does

A URL comes in — from a live browser navigation (extension) or a manual check (dashboard). It gets a verdict in under a second from a two-model ensemble, then a background worker cross-checks it against VirusTotal, Google Safe Browsing, live WHOIS, and SSL certificate data. If the verdict changes, every connected client finds out over a WebSocket without asking. Confirmed-malicious domains sync into the extension's native blocklist, so repeat visits are blocked instantly.

<br>
🏗 Architecture
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

The fast path never touches the network beyond the request itself. WHOIS, SSL handshakes, and external API calls all happen in the background task, so a scan always returns in well under a second — regardless of how slow those checks are.

<br>
✨ Features
<table> <tr> <td width="50%" valign="top">

🔍 Detection

Random Forest over 25+ lexical/domain/SSL features
Independent character n-gram second-opinion model, ensembled
SHAP explainability with a hard timeout
Typosquat detection (Levenshtein vs. curated brands)
Exact-match allowlist guarding against brand-name bias

⚡ Real-time

Async two-phase scanning: instant heuristic → background deep scan → WebSocket push
Live activity feed & debounced live-as-you-type preview
Proactive extension blocklist sync
Toast notifications for live threats
</td> <td width="50%" valign="top">

🌐 Threat Intelligence

VirusTotal + Google Safe Browsing fusion (optional, degrades gracefully)
Geo-IP threat-origin leaderboard
Model version + drift monitoring vs. training baseline
Feature-importance introspection

🎛 Dashboard

Sidebar-navigated: Overview / Threats / Analytics / Live Ops / Settings
Command palette (⌘K) — navigate or scan without touching the mouse
Threat detail drawer with full ensemble breakdown
Searchable, filterable, CSV-exportable threat table
Live requests/min, latency percentiles, scan-volume sparkline
</td> </tr> </table> <br>
📊 Real Results

Trained and validated on real, live data — not just static benchmarks:

Metric	Random Forest	Character N-gram
Accuracy (2016 public dataset, 420K URLs)	87%	92%
ROC-AUC	0.94	—
Accuracy (live URLhaus + Tranco, 20K URLs)	100%*	—

<sub>*Investigated, not just reported — see below.</sub>

Two documented, honestly-investigated findings from real testing:

A genuine model-bias bug, found and fixed. The character n-gram model, trained on real phishing data where popular brands are heavily over-represented in the malicious class, learned to distrust the brand names themselves — scoring google.com at 93% malicious. Root-caused to a real 2:1 imbalance in the training sample, then fixed with a small, exact-match allowlist verified to be un-defeatable by domains merely containing a brand name.
A 100%-accuracy result, explained rather than oversold. A live-data training run hit perfect accuracy — investigated and attributed honestly to that dataset's lexical separability (IP-based malware URLs vs. clean top-domain benign URLs), then stress-tested against a harder, hand-constructed typosquat case where the two ensemble models' scores diverged in an informative way (95.3% vs. 38.4%), demonstrating exactly why ensembling two structurally different models catches what either alone would miss.
<br>
🛠 Engineering
	
Tests	48 passing pytest tests, zero network dependency
CI	GitHub Actions, Python 3.11 + 3.12 matrix, lint + test + dashboard build
Docker	Backend, Celery worker, Redis, dashboard — one command up
Docs	Executable EDA notebook, full draft project report, per-folder READMEs
License	MIT
<br>
🧰 Tech Stack
<div align="center"> <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" /> <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" /> <img src="https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white" /> <img src="https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black" /> <img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white" /> <img src="https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white" /> <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" /> <img src="https://img.shields.io/badge/Chrome%20Extension-4285F4?style=for-the-badge&logo=googlechrome&logoColor=white" /> </div> <br> <div align="center">

→ Explore the full repository, docs, and code

</div>
