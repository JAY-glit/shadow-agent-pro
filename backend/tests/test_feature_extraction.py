import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.feature_extraction import extract_lexical_features, shannon_entropy, extract_all_features


class TestShannonEntropy:
    def test_uniform_string_has_low_entropy(self):
        assert shannon_entropy("aaaaaaaa") == 0.0

    def test_random_looking_string_has_higher_entropy(self):
        assert shannon_entropy("a8x2q9zk") > shannon_entropy("aaaaaaaa")

    def test_empty_string(self):
        assert shannon_entropy("") == 0.0


class TestLexicalFeatures:
    def test_detects_ip_address_url(self):
        features = extract_lexical_features("http://192.168.1.1/login")
        assert features["has_ip_address"] is True

    def test_does_not_flag_normal_domain_as_ip(self):
        features = extract_lexical_features("https://www.google.com")
        assert features["has_ip_address"] is False

    def test_detects_shortener(self):
        features = extract_lexical_features("http://bit.ly/3xK9zP")
        assert features["is_shortener"] is True

    def test_detects_https(self):
        features = extract_lexical_features("https://example.com")
        assert features["uses_https"] is True
        features_http = extract_lexical_features("http://example.com")
        assert features_http["uses_https"] is False

    def test_detects_at_symbol_trick(self):
        features = extract_lexical_features("http://google.com@evil.com/phish")
        assert features["has_at_symbol"] is True

    def test_brand_in_subdomain_flagged(self):
        features = extract_lexical_features("http://paypal.evil-domain.tk/login")
        assert features["brand_in_subdomain_not_domain"] is True

    def test_legitimate_brand_domain_not_flagged(self):
        features = extract_lexical_features("https://www.paypal.com/signin")
        assert features["brand_in_subdomain_not_domain"] is False

    def test_url_length_is_measured(self):
        short = extract_lexical_features("http://a.co")
        long = extract_lexical_features("http://a.co/" + "x" * 200)
        assert long["url_length"] > short["url_length"]


class TestFullFeatureExtraction:
    def test_skip_whois_avoids_network_call(self):
        """skip_whois=True must return instantly and never attempt a real
        WHOIS lookup — this is the core guarantee the fast scan path
        depends on."""
        import time

        start = time.time()
        features = extract_all_features("http://example-test-domain-12345.com", skip_whois=True)
        elapsed = time.time() - start

        assert features["domain_age_days"] == -1
        assert features["domain_is_new"] is False
        assert elapsed < 2.0, f"skip_whois=True took {elapsed:.2f}s — should be near-instant"

    def test_returns_all_expected_feature_keys(self):
        from ml.feature_extraction import FEATURE_ORDER

        features = extract_all_features("https://example.com", skip_whois=True)
        for key in FEATURE_ORDER:
            assert key in features, f"missing expected feature: {key}"
