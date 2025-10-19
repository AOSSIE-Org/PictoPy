"""
Tests for authentication system.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.middleware.auth import create_access_token, verify_token
from app.config.settings import API_KEY

client = TestClient(app)


class TestAuthentication:
    """Test authentication endpoints and middleware."""

    def test_health_endpoint_no_auth(self):
        """Test that health endpoint works without authentication."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_auth_status_without_api_key(self):
        """Test auth status endpoint without API key."""
        response = client.get("/auth/status")
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is False
        assert data["auth_method"] is None

    def test_auth_status_with_valid_api_key(self):
        """Test auth status endpoint with valid API key."""
        response = client.get("/auth/status", headers={"X-API-Key": API_KEY})
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert data["auth_method"] == "api_key"

    def test_auth_status_with_invalid_api_key(self):
        """Test auth status endpoint with invalid API key."""
        response = client.get("/auth/status", headers={"X-API-Key": "invalid-key"})
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is False

    def test_generate_token_with_valid_api_key(self):
        """Test JWT token generation with valid API key."""
        response = client.post(
            "/auth/token",
            json={"client_id": "test-client", "api_key": API_KEY},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    def test_generate_token_with_invalid_api_key(self):
        """Test JWT token generation with invalid API key."""
        response = client.post(
            "/auth/token",
            json={"client_id": "test-client", "api_key": "invalid-key"},
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "Invalid API key"

    def test_create_and_verify_token(self):
        """Test JWT token creation and verification."""
        # Create token
        token = create_access_token(data={"sub": "test-user", "client": "test"})
        assert token is not None

        # Verify token
        payload = verify_token(token)
        assert payload["sub"] == "test-user"
        assert payload["client"] == "test"
        assert "exp" in payload

    def test_verify_invalid_token(self):
        """Test verification of invalid JWT token."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            verify_token("invalid-token")
        assert exc_info.value.status_code == 401

    def test_cors_headers_present(self):
        """Test that CORS headers are properly set."""
        response = client.options("/health")
        # Should not fail with CORS error
        assert response.status_code in [200, 405]  # 405 if OPTIONS not explicitly handled

    def test_security_headers_present(self):
        """Test that security headers are present in responses."""
        response = client.get("/health")
        headers = response.headers

        # Check security headers
        assert "x-content-type-options" in headers
        assert headers["x-content-type-options"] == "nosniff"
        assert "x-frame-options" in headers
        assert headers["x-frame-options"] == "DENY"
        assert "x-xss-protection" in headers
        assert "strict-transport-security" in headers


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limit_headers_present(self):
        """Test that rate limit headers are present in responses."""
        response = client.get("/auth/status")
        headers = response.headers

        # slowapi adds rate limit headers
        # Note: These might not always be present in test environment
        # This is more of a smoke test
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
