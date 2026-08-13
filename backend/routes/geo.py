from flask import Blueprint, jsonify
from sqlalchemy import func

from models.database import db, Threat
from utils.geoip import geolocate_domain
from auth import require_auth

geo_bp = Blueprint("geo", __name__, url_prefix="/api/geo")


@geo_bp.route("/threats", methods=["GET"])
@require_auth
def geo_threats():
    """Geolocates the distinct malicious domains seen so far and returns
    points for the dashboard's threat-origin map, plus a per-country
    rollup for a simple leaderboard view."""
    domains = (
        db.session.query(Threat.domain, func.count(Threat.id).label("count"))
        .filter(Threat.verdict == "malicious")
        .group_by(Threat.domain)
        .order_by(func.count(Threat.id).desc())
        .limit(30)
        .all()
    )

    points = []
    country_counts = {}

    for domain, count in domains:
        geo = geolocate_domain(domain)
        if not geo or geo.get("lat") is None:
            continue
        points.append(
            {
                "domain": domain,
                "count": count,
                "lat": geo["lat"],
                "lon": geo["lon"],
                "country": geo.get("country"),
                "city": geo.get("city"),
            }
        )
        country = geo.get("country")
        if country:
            country_counts[country] = country_counts.get(country, 0) + count

    leaderboard = sorted(
        [{"country": c, "count": n} for c, n in country_counts.items()],
        key=lambda x: x["count"],
        reverse=True,
    )

    return jsonify({"points": points, "leaderboard": leaderboard})
