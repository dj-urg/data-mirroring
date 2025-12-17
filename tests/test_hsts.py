import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    # Ensure TRUSTED_HOSTS includes localhost for testing
    import os
    os.environ['TRUSTED_HOSTS'] = 'localhost,127.0.0.1'
    # Ensure CORS_ALLOWED_ORIGINS is set
    os.environ['CORS_ALLOWED_ORIGINS'] = 'http://localhost:5001'
    
    with app.test_client() as client:
        yield client

def test_hsts_header_present_on_https_request(client):
    """
    Test that Strict-Transport-Security header is present when 
    request is secure (simulated via X-Forwarded-Proto).
    """
    # Simulate an HTTPS request coming from a proxy
    response = client.get('/enter-code', headers={'X-Forwarded-Proto': 'https'})
    
    # We expect 200 OK because /enter-code is public
    assert response.status_code == 200
    assert 'Strict-Transport-Security' in response.headers
    assert response.headers['Strict-Transport-Security'] == 'max-age=31536000; includeSubDomains; preload'

def test_hsts_header_missing_on_http_request(client):
    """
    Test that Strict-Transport-Security header is MISSING when 
    request is NOT secure.
    """
    # Simulate an HTTP request
    response = client.get('/enter-code', headers={'X-Forwarded-Proto': 'http'})
    
    assert response.status_code == 200
    # Should NOT have HSTS header on insecure connection
    assert 'Strict-Transport-Security' not in response.headers
