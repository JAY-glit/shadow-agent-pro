"""
feature_extraction.py

Extracts 25+ lexical, domain, SSL, and WHOIS-based features from a URL for
the Random Forest classifier. Designed to be shared between offline training
(ml-training/train.py) and the live Flask prediction path (ml/predict.py).
"""

import re
import socket
import ssl
import math
from datetime import datetime, timezone
from urllib.parse import urlparse

import tldextract

SHORTENER_DOMAINS = {"bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", "is.gd"}
BRAND_KEYWORDS = ["paypal", "google", "microsoft", "apple", "amazon", "netflix", "bank"]


def shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    probs = [s.count(c) / len(s) for c in set(s)]
    return -sum(p * math.log2(p) for p in probs)


def extract_lexical_features(url: str) -> dict:
    parsed = urlparse(url)
    ext = tldextract.extract(url)
    host = parsed.netloc

    return {
        "url_length": len(url),
        "hostname_length": len(host),
        "path_length": len(parsed.path),
        "num_dots": url.count("."),
        "num_hyphens": url.count("-"),
        "num_underscores": url.count("_"),
        "num_slashes": url.count("/"),
        "num_digits": sum(c.isdigit() for c in url),
        "num_special_chars": len(re.findall(r"[^a-zA-Z0-9./:-]", url)),
        "num_subdomains": max(len(ext.subdomain.split(".")), 0) if ext.subdomain else 0,
        "has_ip_address": bool(re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ext.domain)),
        "is_shortener": ext.registered_domain in SHORTENER_DOMAINS,
        "has_at_symbol": "@" in url,
        "has_double_slash_redirect": url.rfind("//") > 7,
        "uses_https": parsed.scheme == "https",
        "entropy": shannon_entropy(host),
        "brand_keyword_count": sum(1 for b in BRAND_KEYWORDS if b in host.lower()),
        "brand_in_subdomain_not_domain": any(
            b in ext.subdomain.lower() and b not in ext.domain.lower() for b in BRAND_KEYWORDS
        ),
    }


def extract_domain_age_days(domain: str, timeout: float = 3.0) -> int:
    """Returns domain age in days, or -1 if lookup fails/unavailable.
    Enforces a short socket timeout — WHOIS servers for non-existent or
    unusual domains can otherwise hang for 20-30+ seconds per lookup,
    which is fatal when extracting features for thousands of URLs during
    training."""
    import socket

    try:
        import whois  # python-whois

        previous_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(timeout)
        try:
            info = whois.whois(domain)
        finally:
            socket.setdefaulttimeout(previous_timeout)

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


def extract_ssl_features(hostname: str) -> dict:
    """Connects on 443 and pulls certificate validity/expiry/CN-match info."""
    features = {
        "has_valid_ssl": False,
        "ssl_days_to_expiry": -1,
        "ssl_self_signed": False,
        "ssl_cn_mismatch": True,
    }
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=3) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                not_after = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
                features["ssl_days_to_expiry"] = (not_after - datetime.utcnow()).days
                features["has_valid_ssl"] = True

                cn_matches = any(
                    hostname == name or hostname.endswith("." + name.lstrip("*."))
                    for field in cert.get("subjectAltName", [])
                    for name in [field[1]]
                )
                features["ssl_cn_mismatch"] = not cn_matches
    except ssl.SSLCertVerificationError:
        features["ssl_self_signed"] = True
    except Exception:
        pass
    return features


def extract_all_features(url: str, skip_whois: bool = False) -> dict:
    """Master function combining all 25+ features into a single dict,
    matching the column order expected by the trained model.

    skip_whois=True bypasses the domain-age lookup entirely (age is
    recorded as unknown/-1). Useful for synthetic/test datasets where the
    domains don't really exist and every lookup would otherwise burn
    several seconds hitting a timeout for no informational gain."""
    parsed = urlparse(url)
    ext = tldextract.extract(url)
    domain = ext.registered_domain

    features = {}
    features.update(extract_lexical_features(url))
    features.update(extract_ssl_features(parsed.netloc))

    age = -1 if skip_whois else extract_domain_age_days(domain)
    features["domain_age_days"] = age
    features["domain_is_new"] = age != -1 and age < 30

    return features


FEATURE_ORDER = [
    "url_length", "hostname_length", "path_length", "num_dots", "num_hyphens",
    "num_underscores", "num_slashes", "num_digits", "num_special_chars",
    "num_subdomains", "has_ip_address", "is_shortener", "has_at_symbol",
    "has_double_slash_redirect", "uses_https", "entropy", "brand_keyword_count",
    "brand_in_subdomain_not_domain", "has_valid_ssl", "ssl_days_to_expiry",
    "ssl_self_signed", "ssl_cn_mismatch", "domain_age_days", "domain_is_new",
]
