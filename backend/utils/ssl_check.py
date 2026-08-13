"""ssl_check.py — validates a host's SSL certificate: validity, expiry,
self-signed status, and CN/SAN hostname match."""

import socket
import ssl
from datetime import datetime


def check_ssl(hostname: str, port: int = 443, timeout: float = 3.0) -> dict:
    result = {
        "valid": False,
        "days_to_expiry": -1,
        "self_signed": False,
        "cn_match": False,
        "issuer": None,
    }
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                result["valid"] = True

                not_after = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
                result["days_to_expiry"] = (not_after - datetime.utcnow()).days

                issuer = dict(x[0] for x in cert.get("issuer", []))
                result["issuer"] = issuer.get("organizationName", "Unknown")

                sans = [v for k, v in cert.get("subjectAltName", []) if k == "DNS"]
                result["cn_match"] = hostname in sans or any(
                    hostname.endswith(s.lstrip("*")) for s in sans
                )
    except ssl.SSLCertVerificationError:
        result["self_signed"] = True
    except (socket.timeout, socket.gaierror, ConnectionRefusedError, OSError):
        pass

    return result
