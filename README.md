<div align="center">

# 🛡️ Shadow Agent Pro

**Real-time malicious URL detection system — Chrome extension + ML backend + live dashboard**

![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-REST_API-000000?style=flat-square&logo=flask&logoColor=white)
![React](https://img.shields.io/badge/React-Dashboard-61DAFB?style=flat-square&logo=react&logoColor=black)
![Chrome MV3](https://img.shields.io/badge/Chrome-MV3_Extension-4285F4?style=flat-square&logo=googlechrome&logoColor=white)
![Tests](https://img.shields.io/badge/tests-48_passing-brightgreen?style=flat-square)
![CI](https://img.shields.io/badge/CI-GitHub_Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square)

</div>

<br>

## Overview

Shadow Agent Pro is a three-tier system that intercepts and classifies
malicious URLs in real time. It started as a Chrome MV3 extension + Flask
backend + React dashboard built under deadline pressure, and evolved into a
production-quality threat detection platform with a two-model ML ensemble,
explainable predictions, async deep scanning, and live monitoring.

Built as a B.Tech Computer Science (AI) capstone project by **Jay Durga**
(enrollment 221020110013) and **Ranjith Kumar** (enrollment 221020110030).

<br>

## Architecture

```
┌─────────────────────┐      ┌──────────────────────┐      ┌─────────────────────┐
│   Chrome Extension   │─────▶│      Flask API        │─────▶│   React Dashboard    │
│   (Manifest V3)      │      │   (ML inference +      │◀─────│   (Vite, live view)  │
│   Persistent worker  │◀─────│    business logic)     │      │   WebSocket client   │
└─────────────────────┘      └──────────────────────┘      └─────────────────────┘
                                        │
                        ┌───────────────┼────────────────┐
                        ▼               ▼                ▼
                 ┌────────────┐  ┌────────────┐   ┌──────────────┐
                 │   Redis     │  │   Celery    │   │  Model Drift  │
                 │  (cache +   │  │ (async deep │   │   Monitor     │
                 │  fallback)  │  │    scan)    │   │               │
                 └────────────┘  └────────────┘   └──────────────┘
```

<br>

## Features

### Detection Engine
- **Two-model ensemble**
  - Random Forest classifier trained on 27 handcrafted URL features
  - Character n-gram TF-IDF + Logistic Regression for lexical pattern detection
  - Combined ensemble decision, ~90% detection accuracy
- **SHAP explainability** — every flagged URL returns the specific features
  that drove the decision, with hard timeouts so explanation generation
  never blocks the response
- **Typosquatting detection** — flags domains designed to impersonate
  legitimate sites
- **Geo-IP threat mapping** — visualizes where flagged traffic originates
- **Model drift monitoring** — tracks classifier accuracy over time and
  surfaces degradation before it becomes a problem

### Backend
- JWT authentication
- Redis caching with automatic in-memory fallback if Redis is unavailable
- Async deep-scan pipeline via Celery for expensive analysis that
  shouldn't block the main request path
- WebSocket live push so the dashboard reflects new detections instantly
- Bootstrap script for one-command environment setup

### Extension
- Chrome Manifest V3, persistent service worker
- Live URL interception at the browser level

### Dashboard
- React + Vite
- Real-time threat feed via WebSocket
- Geo-IP threat map view

### Quality
- 48 passing pytest tests
- GitHub Actions CI on every push
- Verified through live testing on Windows PowerShell with Python 3.14

<br>

## Tech Stack

| Layer | Technology |
|---|---|
| Extension | Chrome Manifest V3, Service Workers |
| Backend API | Flask, JWT |
| ML | Scikit-learn (Random Forest), TF-IDF + Logistic Regression, SHAP |
| Async processing | Celery |
| Caching | Redis (with in-memory fallback) |
| Real-time | WebSocket |
| Frontend | React, Vite |
| Testing / CI | pytest, GitHub Actions |
| Containerization | Docker |

<br>

## Getting Started

```bash
# Clone the repository
git clone https://github.com/JAY-glit/shadow-agent-pro.git
cd shadow-agent-pro

# Run the bootstrap script — sets up backend, dependencies, and env
./bootstrap.sh        # or bootstrap.ps1 on Windows

# Start the backend
cd backend
python app.py

# Start the dashboard
cd ../dashboard
npm install
npm run dev

# Load the extension
# Go to chrome://extensions → Enable Developer Mode → Load Unpacked → select /extension
```

<br>

## Testing

```bash
cd backend
pytest
```

48 tests covering the ML pipeline, API endpoints, caching fallback
behavior, and authentication. CI runs automatically via GitHub Actions on
every push.

<br>

## Project Structure

```
shadow-agent-pro/
├── extension/          # Chrome MV3 extension
├── backend/             # Flask API, ML models, Celery tasks
│   ├── models/           # Trained classifiers
│   ├── tests/             # pytest suite (48 tests)
│   └── app.py
├── dashboard/            # React + Vite frontend
├── bootstrap.sh          # One-command setup
└── .github/workflows/    # CI pipeline
```

<br>

## Team

- **Jay Durga** — [GitHub](https://github.com/JAY-glit) · [LinkedIn](https://www.linkedin.com/in/jaydurga/)
- **Ranjith Kumar** — Co-developer

Supervised by Dr. Dinesh, Om Sterling Global University, Hisar
(HOD: Dr. Parveen Seghal).

<br>

## License

MIT
