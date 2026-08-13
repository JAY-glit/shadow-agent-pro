import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import metrics


class TestMetricsTracker:
    def setup_method(self):
        metrics.reset()

    def test_empty_snapshot_has_zero_values(self):
        snap = metrics.get_snapshot()
        assert snap["total_requests"] == 0
        assert snap["avg_latency_ms"] == 0
        assert snap["requests_per_minute"] == 0

    def test_records_total_and_verdict_counts(self):
        metrics.record_scan(100, "safe")
        metrics.record_scan(200, "malicious")
        metrics.record_scan(150, "safe")

        snap = metrics.get_snapshot()
        assert snap["total_requests"] == 3
        assert snap["by_verdict"]["safe"] == 2
        assert snap["by_verdict"]["malicious"] == 1

    def test_average_latency_is_correct(self):
        metrics.record_scan(100, "safe")
        metrics.record_scan(200, "safe")
        snap = metrics.get_snapshot()
        assert snap["avg_latency_ms"] == 150.0

    def test_p50_and_p95_are_sane(self):
        for lat in [10, 20, 30, 40, 50, 60, 70, 80, 90, 1000]:
            metrics.record_scan(lat, "safe")
        snap = metrics.get_snapshot()
        # p95 should reflect the outlier, p50 should not
        assert snap["p95_latency_ms"] == 1000
        assert snap["p50_latency_ms"] < 1000

    def test_recent_requests_counted_in_last_minute(self):
        metrics.record_scan(100, "safe")
        snap = metrics.get_snapshot()
        assert snap["requests_per_minute"] == 1

    def test_volume_series_has_entries_after_recording(self):
        metrics.record_scan(100, "safe")
        metrics.record_scan(110, "safe")
        snap = metrics.get_snapshot()
        assert len(snap["volume_series"]) >= 1
        assert snap["volume_series"][-1]["count"] >= 1
