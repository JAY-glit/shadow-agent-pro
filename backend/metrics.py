"""
metrics.py — a lightweight, in-memory real-time metrics tracker for the
scan pipeline. This is what powers the "Live Ops" dashboard tab: requests
per minute, rolling latency percentiles, and a time-bucketed scan-volume
series for the live sparkline.

Deliberately in-memory rather than persisted — this is operational
telemetry for "what's happening right now", not historical record (that's
what the Threat/ScanLog tables are for). Resets on restart, which is fine
for what it's used for.

Thread-safe via a simple lock: the Flask dev server is single-threaded by
default, but a production WSGI server or the Celery worker touching this
in the future would not be, so the lock costs nothing now and prevents a
real bug later.
"""

import time
import threading
from collections import deque

_LOCK = threading.Lock()

_REQUEST_TIMESTAMPS = deque(maxlen=1000)  # for requests/minute
_LATENCY_SAMPLES = deque(maxlen=200)  # for p50/p95 latency
_VOLUME_BUCKETS = deque(maxlen=30)  # (bucket_start_epoch, count) per 10s bucket, for the sparkline
_BUCKET_SECONDS = 10

_total_requests = 0
_total_by_verdict = {"safe": 0, "suspicious": 0, "malicious": 0}


def record_scan(latency_ms: int, verdict: str):
    global _total_requests
    now = time.time()

    with _LOCK:
        _total_requests += 1
        _total_by_verdict[verdict] = _total_by_verdict.get(verdict, 0) + 1
        _REQUEST_TIMESTAMPS.append(now)
        _LATENCY_SAMPLES.append(latency_ms)

        bucket_start = int(now // _BUCKET_SECONDS) * _BUCKET_SECONDS
        if _VOLUME_BUCKETS and _VOLUME_BUCKETS[-1][0] == bucket_start:
            ts, count = _VOLUME_BUCKETS[-1]
            _VOLUME_BUCKETS[-1] = (ts, count + 1)
        else:
            _VOLUME_BUCKETS.append((bucket_start, 1))


def _percentile(samples, pct):
    if not samples:
        return 0
    ordered = sorted(samples)
    idx = min(int(len(ordered) * pct), len(ordered) - 1)
    return ordered[idx]


def get_snapshot() -> dict:
    with _LOCK:
        now = time.time()
        one_minute_ago = now - 60
        requests_last_minute = sum(1 for t in _REQUEST_TIMESTAMPS if t >= one_minute_ago)

        latency_list = list(_LATENCY_SAMPLES)
        avg_latency = round(sum(latency_list) / len(latency_list), 1) if latency_list else 0

        volume_series = [
            {"time": bucket_start, "count": count} for bucket_start, count in _VOLUME_BUCKETS
        ]

        return {
            "total_requests": _total_requests,
            "requests_per_minute": requests_last_minute,
            "avg_latency_ms": avg_latency,
            "p50_latency_ms": _percentile(latency_list, 0.5),
            "p95_latency_ms": _percentile(latency_list, 0.95),
            "by_verdict": dict(_total_by_verdict),
            "volume_series": volume_series,
        }


def reset():
    """Test-only helper to reset global state between test runs."""
    global _total_requests
    with _LOCK:
        _total_requests = 0
        _total_by_verdict.clear()
        _total_by_verdict.update({"safe": 0, "suspicious": 0, "malicious": 0})
        _REQUEST_TIMESTAMPS.clear()
        _LATENCY_SAMPLES.clear()
        _VOLUME_BUCKETS.clear()
