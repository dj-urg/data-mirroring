import pytest
from app.utils.security import apply_security_headers, requires_authentication
from app.utils.config import configure_app
from flask import Flask, session, g

# --- Config Assessment Tests ---

def test_production_config_values(mocker):
    """Assess if configure_app correctly applies production security settings."""
    app = Flask(__name__)
    
    # Mock environment to Production
    mocker.patch('os.getenv', side_effect=lambda k, d=None: 'production' if k == 'FLASK_ENV' else d)
    
    configure_app(app)
    
    # Assertions for Key Security Configs
    assert app.config['SESSION_COOKIE_SECURE'] is True
    assert app.config['SESSION_COOKIE_HTTPONLY'] is True
    assert app.config['SESSION_COOKIE_SAMESITE'] == 'Strict'
    assert app.config['WTF_CSRF_SSL_STRICT'] is True

def test_development_config_values(mocker):
    """Assess if configure_app allows relaxed settings in development."""
    app = Flask(__name__)
    
    # Mock environment to Development
    mocker.patch('os.getenv', side_effect=lambda k, d=None: 'development' if k == 'FLASK_ENV' else d)
    
    configure_app(app)
    
    # Assertions for Dev Configs
    assert app.config['SESSION_COOKIE_SECURE'] is False
    assert app.config['SESSION_COOKIE_HTTPONLY'] is True
    assert app.config['SESSION_COOKIE_SAMESITE'] == 'Lax'

# --- Security Headers Assessment Tests ---

def test_apply_security_headers(client):
    """Assess if apply_security_headers adds all critical headers."""
    # We need a request context for 'g.csp_nonce'
    with client.application.test_request_context():
        # Mock nonce
        g.csp_nonce = 'test_nonce_value'
        
        # Create a dummy response
        from flask import make_response
        response = make_response("Content")
        
        # Apply headers
        response = apply_security_headers(response)
        
        # Verify Critical Headers
        headers = response.headers
        
        # CSP
        assert "Content-Security-Policy" in headers
        assert "nonce-test_nonce_value" in headers["Content-Security-Policy"]
        assert "default-src 'none'" in headers["Content-Security-Policy"]
        
        # HSTS (requires secure request usually, but let's check function logic if it mocks request.is_secure)
        # Note: apply_security_headers checks 'if request.is_secure'. 
        # In test_request_context default is http, so HSTS might miss unless we set scheme.
        
        # X-Content-Type-Options
        assert headers["X-Content-Type-Options"] == "nosniff"
        
        # X-Frame-Options
        assert headers["X-Frame-Options"] == "DENY"
        
        # Referrer-Policy
        assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_hsts_header_on_secure_request(client):
    """Assess if HSTS is applied only on secure requests."""
    with client.application.test_request_context(base_url='https://example.com'):
        g.csp_nonce = 'test'
        from flask import make_response
        response = make_response("Content")
        
        response = apply_security_headers(response)
        
        assert "Strict-Transport-Security" in response.headers
        assert "max-age=31536000" in response.headers["Strict-Transport-Security"]

# --- Authentication Decorator Assessment Tests ---

def test_requires_authentication_redirects_unauth(client):
    """Assess if decorator redirects unauthenticated users."""
    
    # Create a protected dummy view
    @client.application.route('/test_protected')
    @requires_authentication
    def protected_view():
        return "Secret Data"
        
    response = client.get('/test_protected')
    
    # Should redirect
    assert response.status_code == 302
    assert '/enter-code' in response.headers['Location']

def test_requires_authentication_allows_auth(client):
    """Assess if decorator allows authenticated users."""
    
    # Create a protected dummy view
    @client.application.route('/test_protected_allowed')
    @requires_authentication
    def protected_view_allowed():
        return "Secret Data"
    
    with client.session_transaction() as sess:
        sess['authenticated'] = True
        
    response = client.get('/test_protected_allowed')
    
    assert response.status_code == 200
    assert b"Secret Data" in response.data
