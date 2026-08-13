"""
routes — Flask Blueprints, one per resource: scan, threats, stats, auth,
geo, model, status, and metrics. Every route except /api/auth/token,
/api/feedback, and /api/health requires a JWT via the @require_auth
decorator (see auth.py).
"""
