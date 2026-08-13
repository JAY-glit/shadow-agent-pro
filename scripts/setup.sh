#!/usr/bin/env bash
# One-shot local dev setup for Shadow Agent Pro (no Docker required).
set -e

echo "== Backend =="
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
echo "Backend deps installed. Run 'python app.py' inside backend/ to start the API."
deactivate
cd ..

echo "== Dashboard =="
cd dashboard
npm install
echo "Dashboard deps installed. Run 'npm run dev' inside dashboard/ to start the UI."
cd ..

echo ""
echo "Next steps:"
echo "1. Start Redis:      redis-server (or: docker run -p 6379:6379 redis:7-alpine)"
echo "2. Train the model:  cd ml-training && python train.py --data datasets/urls_labeled.csv"
echo "3. Start backend:    cd backend && python app.py"
echo "4. Start worker:     cd backend && celery -A celery_app.celery_app worker --loglevel=info"
echo "5. Start dashboard:  cd dashboard && npm run dev"
echo "6. Load extension:   chrome://extensions -> Load unpacked -> select extension/"
echo ""
echo "Note: without Redis running, scans still work (heuristic-only, no deep-scan"
echo "refinement or live WebSocket push across processes) — see README for details."
