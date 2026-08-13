"""whois_check.py — thin wrapper around python-whois with caching to avoid
repeated slow lookups for the same domain within a scan burst, and a hard
socket timeout since WHOIS servers can otherwise hang 20-30+ seconds per
lookup for unusual or non-existent domains."""

import socket
from datetime import datetime, timezone
from functools import lru_cache

import whois

LOOKUP_TIMEOUT_SECONDS = 3.0


@lru_cache(maxsize=512)
def get_domain_age_days(domain: str) -> int:
    previous_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(LOOKUP_TIMEOUT_SECONDS)
    try:
        info = whois.whois(domain)
        creation = info.creation_date
        if isinstance(creation, list):
            creation = creation[0]
        if not creation:
            return -1
        if creation.tzinfo is None:
            creation = creation.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - creation).days
    except Exception:
        return -1
    finally:
        socket.setdefaulttimeout(previous_timeout)


def is_newly_registered(domain: str, threshold_days: int = 30) -> bool:
    age = get_domain_age_days(domain)
    return age != -1 and age < threshold_days
