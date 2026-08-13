# Contributing

## Local setup
See the README's Quick Start section. `backend/requirements-dev.txt` adds pytest, coverage, and flake8 on top of the runtime dependencies.

## Before opening a PR
```bash
cd backend
pip install -r requirements-dev.txt
flake8 . --count --select=E9,F63,F7,F82 --exclude=tests   # must be clean
pytest tests/ -v                                            # must pass
```
CI runs both automatically on push/PR (`.github/workflows/ci.yml`), across Python 3.11 and 3.12.

## Adding a new detection signal
1. Add the feature to `backend/ml/feature_extraction.py` and its entry in `FEATURE_ORDER`.
2. Add at least one test in `backend/tests/test_feature_extraction.py` covering both the "flags" and "doesn't false-positive" cases.
3. Retrain (`ml-training/train.py`) — a new feature changes the expected input shape, so old model artifacts won't load correctly against the updated `FEATURE_ORDER`.

## Adding a new API route
Follow the existing pattern in `backend/routes/`: a Blueprint per resource, `@require_auth` on anything that isn't `/api/health` or `/api/auth/token`, and a corresponding test in `backend/tests/`.

## Code style
No enforced formatter currently — match the surrounding code's style. Docstrings that explain *why* a non-obvious decision was made (timeouts, fallback behavior, ordering) are valued more than restating *what* the code does.
