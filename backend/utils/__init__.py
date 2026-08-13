"""
utils — supporting checks and integrations used by the detection
pipeline: WHOIS domain-age lookups, SSL certificate validation,
page-content scanning, typosquat detection, the known-legitimate-domain
allowlist, external threat intelligence (VirusTotal/Safe Browsing),
geo-IP lookups, and the Redis-backed scan cache.

Each module is designed to fail soft — a network hiccup or missing API
key degrades that one signal rather than breaking the scan pipeline.
"""
