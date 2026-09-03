"""
Tests for CORS configuration and preflight OPTIONS handling.
"""
from fastapi.testclient import TestClient
from app.main import app


class TestCorsPreflight:

    def test_options_preflight_allowed_for_vercel_production_domain(self):
        client = TestClient(app)
        response = client.options(
            "/api/v1/auth/signup-org",
            headers={
                "Origin": "https://covenexa.vercel.app",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, Authorization",
            },
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "https://covenexa.vercel.app"
        assert "POST" in response.headers.get("access-control-allow-methods", "")
        assert response.headers.get("access-control-allow-credentials") == "true"

    def test_options_preflight_allowed_for_localhost_frontend(self):
        client = TestClient(app)
        response = client.options(
            "/api/v1/auth/signup-org",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, Authorization",
            },
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

    def test_options_preflight_rejected_for_disallowed_origin(self):
        client = TestClient(app)
        response = client.options(
            "/api/v1/auth/signup-org",
            headers={
                "Origin": "https://unauthorized-domain.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, Authorization",
            },
        )
        assert response.status_code == 400
        assert "access-control-allow-origin" not in response.headers
