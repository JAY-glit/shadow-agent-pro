import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.allowlist import is_known_legitimate, KNOWN_LEGITIMATE_DOMAINS


class TestAllowlist:
    """Regression coverage for a real bug found during manual testing:
    the character n-gram model, trained on real phishing data where
    popular brands are heavily over-represented in the malicious class
    (attackers impersonate them constantly), learned to distrust the
    brand names themselves — flagging https://www.google.com as
    suspicious at 93% confidence purely from character patterns. See
    ml/char_ngram_model.py and utils/allowlist.py docstrings for the
    full investigation."""

    def test_exact_match_is_legitimate(self):
        assert is_known_legitimate("google.com") is True
        assert is_known_legitimate("wikipedia.org") is True

    def test_case_insensitive(self):
        assert is_known_legitimate("Google.com") is True

    def test_brand_impersonation_domain_not_matched(self):
        """This is the critical property: a phishing domain that merely
        CONTAINS a brand name must never match, or the allowlist would
        become a trivial bypass for attackers."""
        assert is_known_legitimate("googlecom-error.com") is False
        assert is_known_legitimate("google-account-verify.tk") is False
        assert is_known_legitimate("paypal-secure-login.tk") is False

    def test_unrelated_domain_not_matched(self):
        assert is_known_legitimate("example.com") is False
        assert is_known_legitimate("some-random-blog.net") is False

    def test_allowlist_is_intentionally_small(self):
        """Documents the design intent: this is a small, curated,
        boring list of global top-traffic domains — not a general
        safety mechanism. If this grows very large, that's a signal
        the design intent has drifted and is worth revisiting."""
        assert len(KNOWN_LEGITIMATE_DOMAINS) < 100
