"""
cache.py — Redis-backed cache for scan results. Repeat lookups of the same
URL (common when a user revisits a page or multiple tabs share a domain)
skip the full feature-extraction + WHOIS + SSL + model pipeline entirely.

Falls back to a no-op in-memory dict if Redis isn't reachable, so local dev
without a Redis server still works — just without persistence across
restarts.
"""

import json
import hashlib
import os

try:
    import redis

    _redis_client = redis.Redis.from_url(
        # 127.0.0.1 rather than "localhost" is deliberate: on Windows,
        # resolving "localhost" often tries IPv6 (::1) first, and if
        # nothing's listening there (a Docker port mapping is typically
        # IPv4-only), the connection has to time out on that attempt
        # before falling back to IPv4 — adding several seconds to every
        # single Redis operation. This was measured directly: scan
        # latency went from sub-second to ~9-10 seconds average the
        # moment Redis-dependent code paths started actually running.
        os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0"),
        socket_connect_timeout=1,
        decode_responses=True,
    )
    _redis_client.ping()
    REDIS_AVAILABLE = True
except Exception:
    _redis_client = None
    REDIS_AVAILABLE = False

_fallback_store = {}

DEFAULT_TTL_SECONDS = 3600  # re-check any URL at most once per hour


def _key(url: str) -> str:
    return "scan:" + hashlib.sha256(url.encode()).hexdigest()


def get_cached_scan(url: str):
    key = _key(url)
    if REDIS_AVAILABLE:
        raw = _redis_client.get(key)
        return json.loads(raw) if raw else None
    return _fallback_store.get(key)


def set_cached_scan(url: str, result: dict, ttl: int = DEFAULT_TTL_SECONDS):
    key = _key(url)
    if REDIS_AVAILABLE:
        _redis_client.setex(key, ttl, json.dumps(result))
    else:
        _fallback_store[key] = result


def invalidate(url: str):
    key = _key(url)
    if REDIS_AVAILABLE:
        _redis_client.delete(key)
    else:
        _fallback_store.pop(key, None)
