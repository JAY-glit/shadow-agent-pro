"""
logging_config.py — structured, consistent logging setup. Every log line
gets a timestamp, level, module, and (via the request-id filter) a short
ID that ties every line from the same HTTP request together — useful once
you have Celery workers and Flask both logging concurrently and need to
trace one request's story across both.
"""

import logging
import sys
import uuid

from flask import g, has_request_context


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        if has_request_context():
            record.request_id = getattr(g, "request_id", "-")
        else:
            record.request_id = "-"
        return True


def configure_logging(app):
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [req:%(request_id)s] %(name)s: %(message)s"
    )
    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())

    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO if not app.debug else logging.DEBUG)

    @app.before_request
    def _assign_request_id():
        g.request_id = uuid.uuid4().hex[:8]
