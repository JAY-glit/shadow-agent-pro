import pytest


class TestTokenIssuance:
    def test_issue_token_returns_valid_jwt(self, client):
        resp = client.post("/api/auth/token", json={"client_id": "test-client"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert "token" in data
        assert data["client_id"] == "test-client"

    def test_issue_token_generates_client_id_if_omitted(self, client):
        resp = client.post("/api/auth/token", json={})
        assert resp.status_code == 200
        assert resp.get_json()["client_id"]  # non-empty


class TestAuthGating:
    def test_protected_route_rejects_missing_token(self, client):
        resp = client.get("/api/threats")
        assert resp.status_code == 401

    def test_protected_route_rejects_malformed_header(self, client):
        resp = client.get("/api/threats", headers={"Authorization": "NotBearer abc123"})
        assert resp.status_code == 401

    def test_protected_route_rejects_garbage_token(self, client):
        resp = client.get("/api/threats", headers={"Authorization": "Bearer not.a.real.jwt"})
        assert resp.status_code == 401

    def test_protected_route_accepts_valid_token(self, client, auth_headers):
        resp = client.get("/api/threats", headers=auth_headers)
        assert resp.status_code == 200

    def test_health_check_needs_no_auth(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200

    def test_metrics_endpoint_requires_auth(self, client):
        resp = client.get("/api/metrics")
        assert resp.status_code == 401

    def test_metrics_endpoint_returns_snapshot_shape(self, client, auth_headers):
        resp = client.get("/api/metrics", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "total_requests" in data
        assert "avg_latency_ms" in data
        assert "volume_series" in data

    def test_feature_importance_requires_auth(self, client):
        resp = client.get("/api/model/feature-importance")
        assert resp.status_code == 401

    def test_feature_importance_reports_no_model_gracefully(self, client, auth_headers):
        """Without a trained model loaded, this should report a clear
        status rather than 500ing — same fail-soft principle as every
        other optional-dependency check in this project."""
        resp = client.get("/api/model/feature-importance", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] in ("model_not_loaded", "unavailable", "ok")
