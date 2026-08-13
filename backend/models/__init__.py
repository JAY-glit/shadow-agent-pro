"""
models — SQLAlchemy ORM models for persisted application state.

See database.py for the schema: Threat (detected/scanned URLs), ScanLog
(every scan attempt, for latency/volume analysis), Whitelist, Statistics,
and Feedback (user-reported false positives/negatives).
"""
