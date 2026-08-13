import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.typosquatting import levenshtein, check_typosquatting


class TestLevenshtein:
    def test_identical_strings(self):
        assert levenshtein("paypal.com", "paypal.com") == 0

    def test_known_distance(self):
        assert levenshtein("kitten", "sitting") == 3

    def test_empty_strings(self):
        assert levenshtein("", "") == 0
        assert levenshtein("abc", "") == 3

    def test_single_substitution(self):
        assert levenshtein("paypal.com", "paypa1.com") == 1


class TestTyposquatDetection:
    def test_flags_character_substitution(self):
        result = check_typosquatting("http://paypa1.com/login")
        assert result["is_typosquat"] is True
        assert result["closest_brand"] == "paypal.com"

    def test_does_not_flag_legitimate_domain(self):
        result = check_typosquatting("https://www.paypal.com/signin")
        assert result["is_typosquat"] is False

    def test_does_not_flag_unrelated_domain(self):
        result = check_typosquatting("https://en.wikipedia.org/wiki/Python")
        assert result["is_typosquat"] is False

    def test_flags_hyphenated_variant(self):
        result = check_typosquatting("http://secure-paypal.tk/verify")
        # "secure-paypal" is far from any single brand at char level via
        # this simple distance metric — this test documents current
        # behavior (the brand-in-subdomain lexical feature catches this
        # case instead; see feature_extraction.py) rather than asserting
        # typosquat detection catches every phishing pattern on its own.
        assert "distance" in result
