"""
char_ngram_model.py — a second, independent classifier trained directly on
character n-grams of the raw URL string, with no manual feature
engineering at all. This is the lightweight, dependency-safe version of
the "character-level deep learning second opinion" idea: a CNN/LSTM would
do something similar but needs TensorFlow/PyTorch, which (given the build
pain already hit with scikit-learn and shap on newer Python releases in
this project) is a real risk to add as a hard dependency. TF-IDF over
character n-grams + Logistic Regression captures a lot of the same
signal — subword patterns like "paypa1", "-secure-", ".tk" — using only
scikit-learn, which is already a required dependency.

Ensembling two independently-trained models that look at the URL from
different angles (hand-engineered lexical/domain/SSL features vs. raw
character patterns) is a legitimate way to catch cases where one
approach's blind spots are the other's strengths, and it's a reasonable
thing to describe in a report as "hybrid classical ML" without overstating
it as deep learning.
"""

import re
import joblib
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"

_SCHEME_RE = re.compile(r"^https?://", re.IGNORECASE)


def normalize_for_char_model(url: str) -> str:
    """Strips the http(s):// scheme before feeding a URL to the character
    n-gram model. This matters more than it looks: training data sourced
    from download_real_dataset.py has every single row uniformly prefixed
    with "http://" (the source dataset had bare domains with no scheme at
    all), so the model has literally never seen "https://" during
    training. Left unstripped, a real HTTPS URL at inference time is
    genuinely out-of-distribution for this model and can cause a
    legitimate site to score as suspicious purely because of scheme text,
    not anything about the domain itself. Whether a URL uses HTTPS is
    already captured separately by the Random Forest's uses_https
    feature — the char n-gram model doesn't need to see it too, and is
    more robust for not seeing it inconsistently."""
    return _SCHEME_RE.sub("", url)


def build_pipeline() -> Pipeline:
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    analyzer="char_wb",  # char n-grams within word boundaries
                    ngram_range=(3, 5),
                    max_features=5000,
                    sublinear_tf=True,
                ),
            ),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )


def train(urls: list[str], labels: list[int]) -> Pipeline:
    normalized = [normalize_for_char_model(u) for u in urls]
    pipeline = build_pipeline()
    pipeline.fit(normalized, labels)
    return pipeline


def save(pipeline: Pipeline, path: Path = None):
    path = path or ARTIFACTS_DIR / "char_ngram_model.joblib"
    joblib.dump(pipeline, path)


class CharNgramClassifier:
    """Loads the saved pipeline and scores a single URL. Fails soft (returns
    None) if the artifact doesn't exist yet, so the ensemble in predict.py
    can fall back to RF-only scoring for anyone who hasn't retrained since
    this feature was added."""

    def __init__(self, path: Path = None):
        self.path = path or ARTIFACTS_DIR / "char_ngram_model.joblib"
        self.pipeline = None
        self._load_attempted = False

    def _ensure_loaded(self):
        if self._load_attempted:
            return
        self._load_attempted = True
        try:
            self.pipeline = joblib.load(self.path)
        except FileNotFoundError:
            self.pipeline = None

    def predict_proba(self, url: str):
        """Returns malicious-class probability, or None if no model is
        available (not yet trained with this feature, or load failed)."""
        self._ensure_loaded()
        if self.pipeline is None:
            return None
        try:
            normalized = normalize_for_char_model(url)
            proba = self.pipeline.predict_proba([normalized])[0]
            classes = list(self.pipeline.named_steps["clf"].classes_)
            return float(proba[classes.index(1)]) if 1 in classes else None
        except Exception:
            return None


char_ngram_classifier = CharNgramClassifier()
