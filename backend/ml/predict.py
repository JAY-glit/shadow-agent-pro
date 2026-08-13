"""
predict.py — loads the trained Random Forest + scaler, scores a URL, and
returns a verdict with SHAP-based human-readable reasons.
"""

import numpy as np
import joblib
from pathlib import Path
import tldextract

from .feature_extraction import extract_all_features, FEATURE_ORDER
from .char_ngram_model import char_ngram_classifier
from utils.allowlist import is_known_legitimate

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"


class ThreatClassifier:
    def __init__(self, model_path=None, scaler_path=None, threshold=0.6):
        self.model_path = model_path or ARTIFACTS_DIR / "random_forest_model.joblib"
        self.scaler_path = scaler_path or ARTIFACTS_DIR / "feature_scaler.joblib"
        self.threshold = threshold
        self.model = None
        self.scaler = None
        self._explainer = None

    def load(self):
        self.model = joblib.load(self.model_path)
        self.scaler = joblib.load(self.scaler_path)

    def _explain(self, X_scaled, feature_dict):
        """Lazily builds a SHAP TreeExplainer and returns top contributing
        features as plain-language reasons. Wrapped with a hard timeout —
        SHAP's TreeExplainer can be very slow (sometimes effectively
        hanging) on some systems, particularly when its C-accelerated
        backend doesn't build cleanly for a given Python version. This is
        the synchronous fast-path, so it must never block the request
        indefinitely; a slow SHAP call degrades to the fallback reasons
        instead of stalling the whole scan."""
        import concurrent.futures

        def _compute():
            import shap

            if self._explainer is None:
                self._explainer = shap.TreeExplainer(self.model)

            shap_values = self._explainer.shap_values(X_scaled)
            contributions = shap_values[1][0] if isinstance(shap_values, list) else shap_values[0]

            ranked = sorted(
                zip(FEATURE_ORDER, contributions), key=lambda x: abs(x[1]), reverse=True
            )[:4]
            return [self._humanize(name, feature_dict.get(name)) for name, val in ranked if val > 0]

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(_compute)
            return future.result(timeout=2.0)
        except Exception:
            # Covers SHAP import failures, computation errors, AND timeouts
            # (concurrent.futures.TimeoutError is an Exception subclass) —
            # any of these should silently fall back, never crash or hang
            # the scan request.
            return []
        finally:
            # wait=False is deliberate: if _compute is still running past
            # the timeout, we do NOT want to block here waiting for it to
            # finish (that would defeat the entire point of the timeout
            # above). The thread is left to finish in the background and
            # get garbage collected — a little wasted CPU on a rare slow
            # call, but the request thread is never held hostage by it.
            executor.shutdown(wait=False)

    @staticmethod
    def _humanize(feature_name, value):
        readable = {
            "domain_is_new": f"Domain registered recently ({feature_dict_note(value)})",
            "has_ip_address": "URL uses a raw IP address instead of a domain name",
            "has_valid_ssl": "No valid SSL certificate detected",
            "brand_in_subdomain_not_domain": "Brand name found in subdomain, not the real domain (spoofing pattern)",
            "is_shortener": "URL uses a link-shortening service",
            "entropy": "Hostname has unusually high character randomness",
            "ssl_self_signed": "SSL certificate is self-signed",
            "has_at_symbol": "URL contains an '@' symbol (common redirect trick)",
        }
        return readable.get(feature_name, f"Signal: {feature_name} = {value}")

    def predict(self, url: str) -> dict:
        if self.model is None:
            self.load()

        # Allowlist short-circuit: a small set of exact-match, globally
        # well-known legitimate domains skip full ML scoring entirely.
        # This exists because both the char n-gram model and (to a lesser
        # extent) the RF's brand-keyword features can learn a genuine but
        # unhelpful pattern from real phishing data — popular brands are
        # heavily over-represented in the malicious class because
        # attackers impersonate them constantly, so a naive model can
        # end up distrusting the brand names themselves. See
        # utils/allowlist.py for the full reasoning and how this differs
        # from a general safety bypass (exact match only, small curated
        # list, doesn't affect detection of brand-impersonating domains).
        registered_domain = tldextract.extract(url).registered_domain
        if is_known_legitimate(registered_domain):
            return {
                "verdict": "safe",
                "confidence": 0.02,
                "reasons": [f"{registered_domain} is a recognized, well-known legitimate domain"],
                "features": {},
                "char_ngram_score": None,
            }

        # skip_whois=True here is intentional: this is the synchronous "fast
        # path" called directly from the Flask request thread, which is
        # supposed to return in well under a second. WHOIS lookups are a
        # network round-trip that can take seconds even with a short
        # timeout — that's exactly what the Celery deep_scan_task exists
        # to do in the background instead. Doing a live WHOIS lookup here
        # would silently turn every scan request into a slow one.
        features = extract_all_features(url, skip_whois=True)
        X = np.array([[features[f] for f in FEATURE_ORDER]], dtype=float)
        X_scaled = self.scaler.transform(X)

        proba = self.model.predict_proba(X_scaled)[0]
        malicious_proba = proba[1] if len(proba) > 1 else proba[0]

        # Ensemble with the character n-gram second-opinion model when
        # available. Two independently-trained models that look at the URL
        # from different angles (hand-engineered features vs. raw
        # character patterns) agreeing is a stronger signal than either
        # alone; when they disagree, average rather than letting either
        # one silently dominate. Falls back to RF-only if no char-ngram
        # artifact has been trained yet (backward compatible with models
        # trained before this feature existed).
        char_ngram_proba = char_ngram_classifier.predict_proba(url)
        if char_ngram_proba is not None:
            malicious_proba = 0.65 * malicious_proba + 0.35 * char_ngram_proba

        if malicious_proba >= self.threshold:
            verdict = "malicious"
        elif malicious_proba >= self.threshold * 0.5:
            verdict = "suspicious"
        else:
            verdict = "safe"

        reasons = self._explain(X_scaled, features)
        if char_ngram_proba is not None and char_ngram_proba >= 0.7:
            reasons.insert(0, "Character-pattern model independently flagged this URL as suspicious")

        return {
            "verdict": verdict,
            "confidence": round(float(malicious_proba), 4),
            "reasons": reasons or self._fallback_reasons(features),
            "features": features,
            "char_ngram_score": round(float(char_ngram_proba), 4) if char_ngram_proba is not None else None,
        }

    @staticmethod
    def _fallback_reasons(features):
        reasons = []
        if features.get("domain_is_new"):
            reasons.append("Domain registered within the last 30 days")
        if features.get("has_ip_address"):
            reasons.append("URL uses a raw IP address")
        if not features.get("has_valid_ssl"):
            reasons.append("No valid SSL certificate")
        if features.get("is_shortener"):
            reasons.append("Uses a URL shortening service")
        return reasons[:4]


def feature_dict_note(value):
    return "age unknown" if value is None else "flagged"


# Module-level singleton used by Flask routes
classifier = ThreatClassifier()
