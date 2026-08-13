"""
geoip.py — resolves a domain's IP and looks up its country/city via the
free ip-api.com endpoint (no key required, ~45 req/min limit). Results are
cached in-process since a given malicious domain's IP rarely changes within
a session, keeping this cheap enough to call on every deep-scan pass.
"""

import socket
from functools import lru_cache

import requests

GEO_API_URL = "http://ip-api.com/json/{ip}?fields=status,country,countryCode,city,lat,lon,isp"


@lru_cache(maxsize=1024)
def resolve_ip(domain: str) -> str | None:
    try:
        return socket.gethostbyname(domain)
    except socket.gaierror:
        return None


@lru_cache(maxsize=1024)
def geolocate_ip(ip: str) -> dict:
    try:
        resp = requests.get(GEO_API_URL.format(ip=ip), timeout=3)
        data = resp.json()
        if data.get("status") != "success":
            return {}
        return {
            "country": data.get("country"),
            "country_code": data.get("countryCode"),
            "city": data.get("city"),
            "lat": data.get("lat"),
            "lon": data.get("lon"),
            "isp": data.get("isp"),
        }
    except requests.RequestException:
        return {}


def geolocate_domain(domain: str) -> dict:
    ip = resolve_ip(domain)
    if not ip:
        return {}
    geo = geolocate_ip(ip)
    return {"ip": ip, **geo}
