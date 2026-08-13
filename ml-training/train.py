"""
train.py — offline training pipeline for Shadow Agent Pro's Random Forest
classifier.

Expects a labeled dataset (CSV) with columns: url, label (0 = benign, 1 = malicious),
built by merging PhishTank + URLhaus (malicious) and Alexa Top 1M (benign).

Usage:
    python train.py --data datasets/urls_labeled.csv --out ../backend/ml/artifacts
"""

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.preprocessing import StandardScaler

sys.path.append(str(Path(__file__).resolve().parent.parent / "backend"))
from ml.feature_extraction import extract_all_features, FEATURE_ORDER  # noqa: E402
from ml.char_ngram_model import train as train_char_ngram, save as save_char_ngram, normalize_for_char_model  # noqa: E402


def build_feature_matrix(df: pd.DataFrame, skip_whois: bool = False, max_workers: int = 20) -> pd.DataFrame:
    """Extracts features for every URL in parallel. WHOIS/SSL checks are
    network I/O, so a thread pool gives a large speedup over doing them
    one at a time — at 3000 URLs, sequential extraction with WHOIS enabled
    can take hours; threaded, it's minutes. With --skip-whois it's seconds."""
    print(f"Extracting features for {len(df)} URLs (skip_whois={skip_whois}, workers={max_workers})...")

    urls = list(df["url"])
    results = [None] * len(urls)

    def _extract(i, url):
        try:
            return i, extract_all_features(url, skip_whois=skip_whois)
        except Exception:
            return i, {f: 0 for f in FEATURE_ORDER}

    completed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_extract, i, url) for i, url in enumerate(urls)]
        for future in as_completed(futures):
            i, features = future.result()
            results[i] = features
            completed += 1
            if completed % 250 == 0 or completed == len(urls):
                print(f"  ...{completed}/{len(urls)}")

    return pd.DataFrame(results)[FEATURE_ORDER]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="CSV with url,label columns")
    parser.add_argument("--out", default="../backend/ml/artifacts")
    parser.add_argument("--n-iter", type=int, default=25, help="RandomizedSearchCV iterations")
    parser.add_argument(
        "--skip-whois",
        action="store_true",
        help="Skip WHOIS domain-age lookups entirely (recommended for synthetic/test "
        "datasets where domains don't really exist — makes extraction near-instant "
        "instead of waiting on lookup timeouts for every URL)",
    )
    parser.add_argument("--workers", type=int, default=20, help="parallel threads for feature extraction")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.data, encoding="utf-8", encoding_errors="replace")
    X_raw = build_feature_matrix(df, skip_whois=args.skip_whois, max_workers=args.workers)
    y = df["label"].values

    scaler = StandardScaler()
    X = scaler.fit_transform(X_raw)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    param_dist = {
        "n_estimators": [100, 200, 300, 500],
        "max_depth": [None, 10, 20, 30, 40],
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf": [1, 2, 4],
        "max_features": ["sqrt", "log2"],
        "class_weight": ["balanced", None],
    }

    base_model = RandomForestClassifier(random_state=42, n_jobs=-1)
    search = RandomizedSearchCV(
        base_model,
        param_distributions=param_dist,
        n_iter=args.n_iter,
        cv=5,
        scoring="f1",
        random_state=42,
        n_jobs=-1,
        verbose=2,
    )

    print("Running RandomizedSearchCV...")
    search.fit(X_train, y_train)
    model = search.best_estimator_
    print(f"Best params: {search.best_params_}")

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    print("\n=== Evaluation ===")
    print(classification_report(y_test, y_pred, target_names=["benign", "malicious"]))
    print(f"ROC-AUC: {roc_auc_score(y_test, y_proba):.4f}")
    print("Confusion matrix:\n", confusion_matrix(y_test, y_pred))

    joblib.dump(model, out_dir / "random_forest_model.joblib")
    joblib.dump(scaler, out_dir / "feature_scaler.joblib")
    print(f"\nSaved model + scaler to {out_dir}/")

    # Train the second-opinion character n-gram model on the same split —
    # independent of the hand-engineered features, so it can catch
    # different patterns (or confirm the RF's verdict, boosting confidence
    # when both agree).
    print("\nTraining character n-gram second-opinion model...")
    urls_train, urls_test, _, _ = train_test_split(
        df["url"].tolist(), y, test_size=0.2, stratify=y, random_state=42
    )
    char_pipeline = train_char_ngram(urls_train, y_train.tolist())
    urls_test_normalized = [normalize_for_char_model(u) for u in urls_test]
    char_test_proba = char_pipeline.predict_proba(urls_test_normalized)[:, list(char_pipeline.named_steps["clf"].classes_).index(1)]
    char_test_pred = (char_test_proba >= 0.5).astype(int)
    print("Character n-gram model evaluation:")
    print(classification_report(y_test, char_test_pred, target_names=["benign", "malicious"]))
    save_char_ngram(char_pipeline, out_dir / "char_ngram_model.joblib")
    print(f"Saved char_ngram_model.joblib to {out_dir}/")

    # Record training metadata for the /api/model/version and /api/model/drift
    # endpoints — baseline_malicious_rate lets the drift monitor detect when
    # live traffic has shifted meaningfully from the training distribution.
    import json
    from datetime import datetime, timezone

    metadata = {
        "version": datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"),
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "baseline_malicious_rate": round(float(np.mean(y_train)), 4),
        "metrics": {
            "roc_auc": round(float(roc_auc_score(y_test, y_proba)), 4),
            "n_train": len(y_train),
            "n_test": len(y_test),
        },
        "best_params": search.best_params_,
    }
    (out_dir / "model_metadata.json").write_text(json.dumps(metadata, indent=2))
    print(f"Wrote model_metadata.json (version {metadata['version']})")


if __name__ == "__main__":
    main()
