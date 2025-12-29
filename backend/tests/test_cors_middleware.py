"""
Comprehensive unit tests for CORS middleware.

This module contains comprehensive unit tests for the CORS (Cross-Origin Resource Sharing)
middleware, covering various scenarios including preflight requests, allowed origins,
custom headers, credentials, and error cases.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Optional


class CORSMiddleware:
    """Mock CORS Middleware class for testing purposes."""
    
    def __init__(
        self,
        app,
        allow_origins: List[str] = None,
        allow_credentials: bool = False,
        allow_methods: List[str] = None,
        allow_headers: List[str] = None,
        expose_headers: List[str] = None,
        max_age: int = 600,
    ):
        """Initialize CORS middleware with configuration."""
        self.app = app
        self.allow_origins = allow_origins or ["*"]
        self.allow_credentials = allow_credentials
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allow_headers = allow_headers or ["*"]
        self.expose_headers = expose_headers or []
        self.max_age = max_age
    
    def is_allowed_origin(self, origin: str) -> bool:
        """Check if the origin is allowed."""
        if "*" in self.allow_origins:
            return True
        return origin in self.allow_origins
    
    def get_allowed_origin(self, origin: str) -> Optional[str]:
        """Get the allowed origin for response header."""
        if self.is_allowed_origin(origin):
            if "*" in self.allow_origins:
                return "*" if not self.allow_credentials else origin
            return origin
        return None
    
    def preflight_handler(self, request):
        """Handle preflight OPTIONS requests."""
        origin = request.headers.get("Origin")
        method = request.headers.get("Access-Control-Request-Method")
        headers = request.headers.get("Access-Control-Request-Headers", "").split(",")
        
        if not self.is_allowed_origin(origin):
            return {"status": 403, "error": "Origin not allowed"}
        
        if method not in self.allow_methods:
            return {"status": 403, "error": "Method not allowed"}
        
        allowed_origin = self.get_allowed_origin(origin)
        response_headers = {
            "Access-Control-Allow-Origin": allowed_origin,
            "Access-Control-Allow-Methods": ", ".join(self.allow_methods),
            "Access-Control-Allow-Headers": ", ".join(self.allow_headers),
            "Access-Control-Max-Age": str(self.max_age),
        }
        
        if self.allow_credentials:
            response_headers["Access-Control-Allow-Credentials"] = "true"
        
        return {"status": 200, "headers": response_headers}
    
    def process_request(self, request):
        """Process incoming requests."""
        origin = request.headers.get("Origin")
        
        if request.method == "OPTIONS":
            return self.preflight_handler(request)
        
        if not origin:
            return None
        
        if not self.is_allowed_origin(origin):
            return {"status": 403, "error": "Origin not allowed"}
        
        return None
    
    def add_cors_headers(self, request, response):
        """Add CORS headers to response."""
        origin = request.headers.get("Origin")
        
        if not origin or not self.is_allowed_origin(origin):
            return response
        
        allowed_origin = self.get_allowed_origin(origin)
        response.headers["Access-Control-Allow-Origin"] = allowed_origin
        
        if self.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        if self.expose_headers:
            response.headers["Access-Control-Expose-Headers"] = ", ".join(
                self.expose_headers
            )
        
        return response


# Test Fixtures
@pytest.fixture
def mock_app():
    """Create a mock application object."""
    return Mock()


@pytest.fixture
def mock_request():
    """Create a mock request object."""
    request = Mock()
    request.headers = {}
    request.method = "GET"
    return request


@pytest.fixture
def mock_response():
    """Create a mock response object."""
    response = Mock()
    response.headers = {}
    return response


@pytest.fixture
def cors_middleware_default(mock_app):
    """Create CORS middleware with default configuration."""
    return CORSMiddleware(mock_app)


@pytest.fixture
def cors_middleware_restricted(mock_app):
    """Create CORS middleware with restricted origins."""
    return CORSMiddleware(
        mock_app,
        allow_origins=["https://example.com", "https://app.example.com"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
        expose_headers=["X-Total-Count", "X-Page"],
        max_age=3600,
    )


@pytest.fixture
def cors_middleware_open(mock_app):
    """Create CORS middleware with open configuration."""
    return CORSMiddleware(
        mock_app,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
    )


# Initialization Tests
class TestCORSMiddlewareInitialization:
    """Tests for CORS middleware initialization."""
    
    def test_initialization_with_defaults(self, mock_app):
        """Test initialization with default configuration."""
        middleware = CORSMiddleware(mock_app)
        assert middleware.app == mock_app
        assert middleware.allow_origins == ["*"]
        assert middleware.allow_credentials is False
        assert middleware.allow_methods == ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        assert middleware.allow_headers == ["*"]
        assert middleware.expose_headers == []
        assert middleware.max_age == 600
    
    def test_initialization_with_custom_origins(self, mock_app):
        """Test initialization with custom allowed origins."""
        origins = ["https://example.com", "https://app.example.com"]
        middleware = CORSMiddleware(mock_app, allow_origins=origins)
        assert middleware.allow_origins == origins
    
    def test_initialization_with_credentials(self, mock_app):
        """Test initialization with credentials support."""
        middleware = CORSMiddleware(mock_app, allow_credentials=True)
        assert middleware.allow_credentials is True
    
    def test_initialization_with_custom_methods(self, mock_app):
        """Test initialization with custom allowed methods."""
        methods = ["GET", "POST"]
        middleware = CORSMiddleware(mock_app, allow_methods=methods)
        assert middleware.allow_methods == methods
    
    def test_initialization_with_custom_headers(self, mock_app):
        """Test initialization with custom allowed headers."""
        headers = ["Content-Type", "Authorization"]
        middleware = CORSMiddleware(mock_app, allow_headers=headers)
        assert middleware.allow_headers == headers
    
    def test_initialization_with_expose_headers(self, mock_app):
        """Test initialization with exposed headers."""
        headers = ["X-Total-Count", "X-Page"]
        middleware = CORSMiddleware(mock_app, expose_headers=headers)
        assert middleware.expose_headers == headers
    
    def test_initialization_with_custom_max_age(self, mock_app):
        """Test initialization with custom max age."""
        middleware = CORSMiddleware(mock_app, max_age=7200)
        assert middleware.max_age == 7200


# Origin Validation Tests
class TestOriginValidation:
    """Tests for origin validation logic."""
    
    def test_is_allowed_origin_with_wildcard(self, cors_middleware_default, mock_request):
        """Test that wildcard origin allows all origins."""
        assert cors_middleware_default.is_allowed_origin("https://example.com") is True
        assert cors_middleware_default.is_allowed_origin("https://any-domain.com") is True
        assert cors_middleware_default.is_allowed_origin("http://localhost:3000") is True
    
    def test_is_allowed_origin_with_specific_origins(self, cors_middleware_restricted):
        """Test origin validation with specific allowed origins."""
        assert (
            cors_middleware_restricted.is_allowed_origin("https://example.com")
            is True
        )
        assert (
            cors_middleware_restricted.is_allowed_origin("https://app.example.com")
            is True
        )
        assert (
            cors_middleware_restricted.is_allowed_origin("https://unauthorized.com")
            is False
        )
    
    def test_is_allowed_origin_exact_match(self, cors_middleware_restricted):
        """Test that origin validation requires exact match."""
        assert (
            cors_middleware_restricted.is_allowed_origin("https://example.com") is True
        )
        assert (
            cors_middleware_restricted.is_allowed_origin("https://example.com/")
            is False
        )
        assert cors_middleware_restricted.is_allowed_origin("http://example.com") is False
    
    def test_is_allowed_origin_case_sensitive(self, cors_middleware_restricted):
        """Test that origin validation is case-sensitive."""
        assert (
            cors_middleware_restricted.is_allowed_origin("https://example.com") is True
        )
        assert (
            cors_middleware_restricted.is_allowed_origin("https://EXAMPLE.COM") is False
        )


# Get Allowed Origin Tests
class TestGetAllowedOrigin:
    """Tests for get_allowed_origin method."""
    
    def test_get_allowed_origin_with_wildcard_no_credentials(self, cors_middleware_default):
        """Test that wildcard origin is returned without credentials."""
        result = cors_middleware_default.get_allowed_origin("https://example.com")
        assert result == "*"
    
    def test_get_allowed_origin_with_wildcard_and_credentials(self, mock_app):
        """Test that specific origin is returned with credentials."""
        middleware = CORSMiddleware(mock_app, allow_origins=["*"], allow_credentials=True)
        result = middleware.get_allowed_origin("https://example.com")
        assert result == "https://example.com"
    
    def test_get_allowed_origin_with_specific_origin(self, cors_middleware_restricted):
        """Test that specific origin is returned for allowed origins."""
        result = cors_middleware_restricted.get_allowed_origin("https://example.com")
        assert result == "https://example.com"
    
    def test_get_allowed_origin_unauthorized(self, cors_middleware_restricted):
        """Test that None is returned for unauthorized origins."""
        result = cors_middleware_restricted.get_allowed_origin("https://unauthorized.com")
        assert result is None


# Preflight Request Tests
class TestPreflightHandler:
    """Tests for preflight OPTIONS request handling."""
    
    def test_preflight_request_success(self, cors_middleware_default, mock_request):
        """Test successful preflight request."""
        mock_request.headers = {
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        }
        
        response = cors_middleware_default.preflight_handler(mock_request)
        
        assert response["status"] == 200
        assert "headers" in response
        assert "Access-Control-Allow-Origin" in response["headers"]
        assert "Access-Control-Allow-Methods" in response["headers"]
        assert "Access-Control-Allow-Headers" in response["headers"]
    
    def test_preflight_request_forbidden_origin(
        self, cors_middleware_restricted, mock_request
    ):
        """Test preflight request with forbidden origin."""
        mock_request.headers = {
            "Origin": "https://unauthorized.com",
            "Access-Control-Request-Method": "POST",
        }
        
        response = cors_middleware_restricted.preflight_handler(mock_request)
        
        assert response["status"] == 403
        assert response["error"] == "Origin not allowed"
    
    def test_preflight_request_forbidden_method(
        self, cors_middleware_restricted, mock_request
    ):
        """Test preflight request with forbidden method."""
        mock_request.headers = {
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "DELETE",
        }
        
        response = cors_middleware_restricted.preflight_handler(mock_request)
        
        assert response["status"] == 403
        assert response["error"] == "Method not allowed"
    
    def test_preflight_request_headers_present(self, cors_middleware_default):
        """Test that all required headers are present in preflight response."""
        mock_request = Mock()
        mock_request.headers = {
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        }
        
        response = cors_middleware_default.preflight_handler(mock_request)
        headers = response["headers"]
        
        assert "Access-Control-Allow-Origin" in headers
        assert "Access-Control-Allow-Methods" in headers
        assert "Access-Control-Allow-Headers" in headers
        assert "Access-Control-Max-Age" in headers
    
    def test_preflight_request_with_credentials(self, cors_middleware_restricted):
        """Test that credentials header is included when enabled."""
        mock_request = Mock()
        mock_request.headers = {
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET",
        }
        
        response = cors_middleware_restricted.preflight_handler(mock_request)
        headers = response["headers"]
        
        assert "Access-Control-Allow-Credentials" in headers
        assert headers["Access-Control-Allow-Credentials"] == "true"
    
    def test_preflight_request_max_age(self, cors_middleware_restricted):
        """Test that max age is correctly set in preflight response."""
        mock_request = Mock()
        mock_request.headers = {
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET",
        }
        
        response = cors_middleware_restricted.preflight_handler(mock_request)
        headers = response["headers"]
        
        assert headers["Access-Control-Max-Age"] == "3600"
    
    def test_preflight_request_allowed_methods(self, cors_middleware_restricted):
        """Test that allowed methods are correctly included."""
        mock_request = Mock()
        mock_request.headers = {
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
        }
        
        response = cors_middleware_restricted.preflight_handler(mock_request)
        headers = response["headers"]
        
        methods = headers["Access-Control-Allow-Methods"]
        assert "GET" in methods
        assert "POST" in methods
        assert "DELETE" not in methods  # Not allowed in restricted middleware
    
    def test_preflight_request_allowed_headers(self, cors_middleware_restricted):
        """Test that allowed headers are correctly included."""
        mock_request = Mock()
        mock_request.headers = {
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET",
        }
        
        response = cors_middleware_restricted.preflight_handler(mock_request)
        headers = response["headers"]
        
        allowed_headers = headers["Access-Control-Allow-Headers"]
        assert "Content-Type" in allowed_headers
        assert "Authorization" in allowed_headers


# Process Request Tests
class TestProcessRequest:
    """Tests for request processing."""
    
    def test_process_options_request_success(self, cors_middleware_default):
        """Test processing OPTIONS request successfully."""
        mock_request = Mock()
        mock_request.method = "OPTIONS"
        mock_request.headers = {
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
        }
        
        response = cors_middleware_default.process_request(mock_request)
        
        assert response["status"] == 200
        assert "headers" in response
    
    def test_process_get_request_with_origin(self, cors_middleware_default):
        """Test processing GET request with origin header."""
        mock_request = Mock()
        mock_request.method = "GET"
        mock_request.headers = {"Origin": "https://example.com"}
        
        response = cors_middleware_default.process_request(mock_request)
        
        # Allowed origin should return None (no error)
        assert response is None
    
    def test_process_request_without_origin(self, cors_middleware_default):
        """Test processing request without origin header."""
        mock_request = Mock()
        mock_request.method = "GET"
        mock_request.headers = {}
        
        response = cors_middleware_default.process_request(mock_request)
        
        # No origin header should return None
        assert response is None
    
    def test_process_request_forbidden_origin(self, cors_middleware_restricted):
        """Test processing request with forbidden origin."""
        mock_request = Mock()
        mock_request.method = "POST"
        mock_request.headers = {"Origin": "https://unauthorized.com"}
        
        response = cors_middleware_restricted.process_request(mock_request)
        
        assert response["status"] == 403
        assert response["error"] == "Origin not allowed"
    
    def test_process_post_request_with_allowed_origin(self, cors_middleware_restricted):
        """Test processing POST request with allowed origin."""
        mock_request = Mock()
        mock_request.method = "POST"
        mock_request.headers = {"Origin": "https://example.com"}
        
        response = cors_middleware_restricted.process_request(mock_request)
        
        assert response is None  # No error


# Add CORS Headers Tests
class TestAddCORSHeaders:
    """Tests for adding CORS headers to responses."""
    
    def test_add_cors_headers_with_allowed_origin(
        self, cors_middleware_default, mock_request, mock_response
    ):
        """Test adding CORS headers with allowed origin."""
        mock_request.headers = {"Origin": "https://example.com"}
        
        result = cors_middleware_default.add_cors_headers(mock_request, mock_response)
        
        assert "Access-Control-Allow-Origin" in result.headers
        assert result.headers["Access-Control-Allow-Origin"] == "*"
    
    def test_add_cors_headers_without_origin(self, cors_middleware_default):
        """Test that no CORS headers are added without origin."""
        mock_request = Mock()
        mock_request.headers = {}
        mock_response = Mock()
        mock_response.headers = {}
        
        cors_middleware_default.add_cors_headers(mock_request, mock_response)
        
        assert "Access-Control-Allow-Origin" not in mock_response.headers
    
    def test_add_cors_headers_with_forbidden_origin(
        self, cors_middleware_restricted, mock_response
    ):
        """Test that no CORS headers are added for forbidden origin."""
        mock_request = Mock()
        mock_request.headers = {"Origin": "https://unauthorized.com"}
        
        cors_middleware_restricted.add_cors_headers(mock_request, mock_response)
        
        assert "Access-Control-Allow-Origin" not in mock_response.headers
    
    def test_add_cors_headers_with_credentials(self, cors_middleware_restricted):
        """Test that credentials header is added when enabled."""
        mock_request = Mock()
        mock_request.headers = {"Origin": "https://example.com"}
        mock_response = Mock()
        mock_response.headers = {}
        
        cors_middleware_restricted.add_cors_headers(mock_request, mock_response)
        
        assert "Access-Control-Allow-Credentials" in mock_response.headers
        assert mock_response.headers["Access-Control-Allow-Credentials"] == "true"
    
    def test_add_cors_headers_expose_headers(self, cors_middleware_restricted):
        """Test that expose headers are added when configured."""
        mock_request = Mock()
        mock_request.headers = {"Origin": "https://example.com"}
        mock_response = Mock()
        mock_response.headers = {}
        
        cors_middleware_restricted.add_cors_headers(mock_request, mock_response)
        
        assert "Access-Control-Expose-Headers" in mock_response.headers
        exposed = mock_response.headers["Access-Control-Expose-Headers"]
        assert "X-Total-Count" in exposed
        assert "X-Page" in exposed
    
    def test_add_cors_headers_no_expose_headers(self, cors_middleware_default):
        """Test that expose headers header is not added when not configured."""
        mock_request = Mock()
        mock_request.headers = {"Origin": "https://example.com"}
        mock_response = Mock()
        mock_response.headers = {}
        
        cors_middleware_default.add_cors_headers(mock_request, mock_response)
        
        assert "Access-Control-Expose-Headers" not in mock_response.headers


# Integration Tests
class TestCORSMiddlewareIntegration:
    """Integration tests for complete CORS middleware workflow."""
    
    def test_complete_cors_flow_with_wildcard(self, cors_middleware_default):
        """Test complete CORS flow with wildcard origin."""
        # Preflight request
        preflight_request = Mock()
        preflight_request.method = "OPTIONS"
        preflight_request.headers = {
            "Origin": "https://client.example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        }
        
        preflight_response = cors_middleware_default.process_request(preflight_request)
        assert preflight_response["status"] == 200
        
        # Actual request
        actual_request = Mock()
        actual_request.method = "POST"
        actual_request.headers = {"Origin": "https://client.example.com"}
        
        process_response = cors_middleware_default.process_request(actual_request)
        assert process_response is None
        
        # Response with headers
        response = Mock()
        response.headers = {}
        
        cors_middleware_default.add_cors_headers(actual_request, response)
        assert "Access-Control-Allow-Origin" in response.headers
    
    def test_complete_cors_flow_restricted(self, cors_middleware_restricted):
        """Test complete CORS flow with restricted origins."""
        # Preflight request
        preflight_request = Mock()
        preflight_request.method = "OPTIONS"
        preflight_request.headers = {
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        }
        
        preflight_response = cors_middleware_restricted.process_request(
            preflight_request
        )
        assert preflight_response["status"] == 200
        
        # Unauthorized preflight request
        unauthorized_preflight = Mock()
        unauthorized_preflight.method = "OPTIONS"
        unauthorized_preflight.headers = {
            "Origin": "https://unauthorized.com",
            "Access-Control-Request-Method": "POST",
        }
        
        unauthorized_response = cors_middleware_restricted.process_request(
            unauthorized_preflight
        )
        assert unauthorized_response["status"] == 403
    
    def test_complete_cors_flow_method_not_allowed(self, cors_middleware_restricted):
        """Test CORS flow when method is not allowed."""
        preflight_request = Mock()
        preflight_request.method = "OPTIONS"
        preflight_request.headers = {
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "DELETE",
        }
        
        response = cors_middleware_restricted.process_request(preflight_request)
        
        assert response["status"] == 403
        assert response["error"] == "Method not allowed"


# Edge Cases and Error Handling Tests
class TestEdgeCasesAndErrors:
    """Tests for edge cases and error handling."""
    
    def test_empty_origin_header(self, cors_middleware_default, mock_request):
        """Test handling of empty origin header."""
        mock_request.headers = {"Origin": ""}
        mock_request.method = "GET"
        
        response = cors_middleware_default.process_request(mock_request)
        
        # Empty origin should not raise error
        assert response is None
    
    def test_malformed_request_headers(self, cors_middleware_default, mock_request):
        """Test handling of malformed request headers."""
        mock_request.headers = None
        mock_request.method = "GET"
        
        # Should handle gracefully
        try:
            response = cors_middleware_default.process_request(mock_request)
        except AttributeError:
            # Expected behavior - headers attribute is required
            pass
    
    def test_multiple_preflight_requests(self, cors_middleware_default):
        """Test handling multiple preflight requests."""
        for i in range(5):
            mock_request = Mock()
            mock_request.method = "OPTIONS"
            mock_request.headers = {
                "Origin": f"https://client{i}.example.com",
                "Access-Control-Request-Method": "GET",
            }
            
            response = cors_middleware_default.process_request(mock_request)
            assert response["status"] == 200
    
    def test_special_characters_in_origin(self, mock_app):
        """Test handling of special characters in origin."""
        middleware = CORSMiddleware(
            mock_app, allow_origins=["https://sub-domain.example.co.uk"]
        )
        
        assert (
            middleware.is_allowed_origin("https://sub-domain.example.co.uk") is True
        )
        assert middleware.is_allowed_origin("https://sub_domain.example.co.uk") is False
    
    def test_origin_with_port_number(self, mock_app):
        """Test handling of origin with port number."""
        middleware = CORSMiddleware(
            mock_app, allow_origins=["https://example.com:8443"]
        )
        
        assert middleware.is_allowed_origin("https://example.com:8443") is True
        assert middleware.is_allowed_origin("https://example.com") is False
    
    def test_origin_with_path_not_allowed(self, mock_app):
        """Test that origin with path is not considered equal."""
        middleware = CORSMiddleware(mock_app, allow_origins=["https://example.com"])
        
        assert middleware.is_allowed_origin("https://example.com") is True
        assert middleware.is_allowed_origin("https://example.com/path") is False


# Performance Tests
class TestCORSMiddlewarePerformance:
    """Tests for CORS middleware performance characteristics."""
    
    def test_origin_lookup_performance(self, cors_middleware_open):
        """Test that origin lookup is efficient."""
        import time
        
        mock_request = Mock()
        mock_request.headers = {"Origin": "https://example.com"}
        
        start = time.time()
        for _ in range(1000):
            cors_middleware_open.is_allowed_origin("https://example.com")
        end = time.time()
        
        # Should complete in reasonable time (< 1 second for 1000 calls)
        assert (end - start) < 1.0
    
    def test_preflight_handling_performance(self, cors_middleware_default):
        """Test that preflight handling is efficient."""
        import time
        
        mock_request = Mock()
        mock_request.headers = {
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
        }
        
        start = time.time()
        for _ in range(100):
            cors_middleware_default.preflight_handler(mock_request)
        end = time.time()
        
        # Should complete in reasonable time (< 0.5 second for 100 calls)
        assert (end - start) < 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
