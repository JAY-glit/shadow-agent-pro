#!/usr/bin/env python3
"""
bootstrap.py — one-command setup for a fresh clone/extraction of this
project. Checks what's missing (Python deps, trained model artifacts,
dashboard deps) and does the minimum work needed to get to a runnable
state, rather than blindly re-running everything every time.

This exists because of a real, repeated pain point: model artifacts are
intentionally NOT shipped in the project zip (they're large binaries),
so every fresh extraction needs retraining before scans work — and that
step is easy to forget, producing a confusing "verdict: error" in the
dashboard with no obvious cause. This script makes that step automatic
and impossible to skip by accident.

Usage:
    python scripts/bootstrap.py            # full setup
    python scripts/bootstrap.py --check    # report status only, no changes
"""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
ML_TRAINING = ROOT / "ml-training"
DASHBOARD = ROOT / "dashboard"
ARTIFACTS = BACKEND / "ml" / "artifacts"

REQUIRED_ARTIFACTS = ["random_forest_model.joblib", "feature_scaler.joblib", "char_ngram_model.joblib"]


def check_status():
    print("=== Shadow Agent Pro — setup status ===\n")

    missing_artifacts = [f for f in REQUIRED_ARTIFACTS if not (ARTIFACTS / f).exists()]
    if missing_artifacts:
        print(f"[ ] Model artifacts — MISSING: {', '.join(missing_artifacts)}")
    else:
        print("[x] Model artifacts — present")

    backend_env_exists = (BACKEND / ".env").exists()
    print(f"[{'x' if backend_env_exists else ' '}] backend/.env — {'present' if backend_env_exists else 'not configured (optional — VirusTotal/Safe Browsing disabled without it)'}")

    dashboard_deps = (DASHBOARD / "node_modules").exists()
    print(f"[{'x' if dashboard_deps else ' '}] Dashboard npm dependencies — {'installed' if dashboard_deps else 'not installed'}")

    try:
        import flask  # noqa: F401
        print("[x] Backend Python dependencies — installed")
        backend_deps = True
    except ImportError:
        print("[ ] Backend Python dependencies — NOT installed")
        backend_deps = False

    print()
    return not missing_artifacts and backend_deps


def run(cmd, cwd, description):
    print(f"→ {description}")
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        print(f"\n✗ Failed: {description}")
        sys.exit(1)
    print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Report status only, make no changes")
    parser.add_argument("--sample-size", type=int, default=3000, help="max-per-class for the real dataset download")
    args = parser.parse_args()

    ready = check_status()

    if args.check:
        sys.exit(0 if ready else 1)

    if ready:
        print("Everything looks set up already — nothing to do.")
        print("Run 'python app.py' in backend/ to start the server.")
        return

    py = sys.executable

    # 1. Backend Python dependencies
    try:
        import flask  # noqa: F401
    except ImportError:
        run([py, "-m", "pip", "install", "-r", "requirements.txt"], BACKEND, "Installing backend dependencies")

    # 2. Model artifacts
    missing_artifacts = [f for f in REQUIRED_ARTIFACTS if not (ARTIFACTS / f).exists()]
    if missing_artifacts:
        dataset_path = ML_TRAINING / "datasets" / "urls_labeled_real.csv"
        run(
            [py, "download_real_dataset.py", "--out", str(dataset_path), "--max-per-class", str(args.sample_size)],
            ML_TRAINING,
            "Downloading real labeled dataset",
        )
        run(
            [py, "train.py", "--data", str(dataset_path), "--out", str(ARTIFACTS), "--skip-whois"],
            ML_TRAINING,
            "Training Random Forest + character n-gram models (this takes a few minutes)",
        )

    # 3. .env template
    env_path = BACKEND / ".env"
    env_example = BACKEND / ".env.example"
    if not env_path.exists() and env_example.exists():
        env_path.write_text(env_example.read_text())
        print("→ Created backend/.env from template (add your own API keys later if you want them)\n")

    print("=== Setup complete ===")
    print("Next steps:")
    print("  cd backend && python app.py")
    print("  cd dashboard && npm install && npm run dev   (only if you want the dashboard)")


if __name__ == "__main__":
    main()
