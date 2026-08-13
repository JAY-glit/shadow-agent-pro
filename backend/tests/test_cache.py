import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.cache import get_cached_scan, set_cached_scan, invalidate, _key


class TestCacheKeying:
    def test_same_url_produces_same_key(self):
        assert _key("http://example.com") == _key("http://example.com")

    def test_different_urls_produce_different_keys(self):
        assert _key("http://example.com") != _key("http://other.com")


class TestCacheRoundTrip:
    """These exercise whichever backend is active (Redis if reachable,
    otherwise the in-memory fallback dict) — the point is the public API
    behaves the same either way, which is the whole reason the fallback
    exists."""

    def test_set_then_get_returns_stored_value(self):
        url = "http://cache-test-example.com/unique-path-12345"
        payload = {"verdict": "safe", "confidence": 0.1}

        set_cached_scan(url, payload)
        result = get_cached_scan(url)

        assert result == payload

    def test_get_missing_key_returns_none(self):
        result = get_cached_scan("http://never-cached-url-xyz-999.com")
        assert result is None

    def test_invalidate_removes_entry(self):
        url = "http://cache-invalidate-test.com"
        set_cached_scan(url, {"verdict": "malicious"})
        invalidate(url)
        assert get_cached_scan(url) is None
