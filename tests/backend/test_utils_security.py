import pytest
from app.utils.security import enforce_https
from unittest.mock import MagicMock

def test_enforce_https_redirect(mocker, client):
    """Test that enforce_https redirects valid HTTP requests to HTTPS in production."""
    # Use test_request_context to mock a request with correct base_url match
    # base_url should match the allowed hosts to avoid 'Invalid redirect' if logic reaches there
    with client.application.test_request_context('/path', headers={'X-Forwarded-Proto': 'http'}, base_url='http://data-mirror.org'):
        # Mock environment: FLASK_ENV=production, DYNO=None
        def getenv_side_effect(key, default=None):
            if key == 'FLASK_ENV':
                return 'production'
            if key == 'DYNO':
                return None
            return default
            
        mocker.patch('os.getenv', side_effect=getenv_side_effect)
        
        # We need to mock g.csp_nonce because apply_security_headers uses it
        from flask import g
        g.csp_nonce = 'test-nonce'
        
        response = enforce_https()
        
        assert response.status_code == 301
        assert response.headers['Location'] == 'https://data-mirror.org/path'

def test_enforce_https_no_redirect_dev(mocker, client):
    """Test that enforce_https does not redirect in development."""
    # Mock environment: FLASK_ENV=development, DYNO=None
    def getenv_side_effect(key, default=None):
        if key == 'FLASK_ENV':
            return 'development'
        return default

    mocker.patch('os.getenv', side_effect=getenv_side_effect)
    
    with client.application.test_request_context('/path'):
        response = enforce_https()
        assert response is None
