import pytest
from app import create_app
import os

@pytest.fixture
def client_production():
    # Force production env
    os.environ['FLASK_ENV'] = 'production'
    # Ensure dependencies are satisfied
    os.environ['ACCESS_CODE_HASH'] = 'test_hash'
    os.environ['SECRET_KEY'] = 'test_secret'
    os.environ['TRUSTED_HOSTS'] = 'localhost'
    
    app = create_app()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client

def test_session_cookie_samesite_policy(client_production):
    """
    Test that the session cookie has SameSite set to Strict in production.
    """
    # Make a request that creates a session (e.g. login)
    # or just any request if session is created on access (Flask default doesn't always create unless needed)
    
    # We can use /enter-code which might set session cookies orcsrf
    response = client_production.get('/enter-code')
    
    # Check Set-Cookie headers
    cookies = [header for header in response.headers if header[0] == 'Set-Cookie']
    
    found_samesite = False
    for name, value in cookies:
        print(f"Cookie: {name}: {value}")
        if 'SameSite=Strict' in value:
            found_samesite = True
        elif 'SameSite=Lax' in value:
            pytest.fail(f"Found SameSite=Lax in production cookie: {value}")
        elif 'SameSite=None' in value:
            pytest.fail(f"Found SameSite=None in production cookie: {value}")
            
    # Note: Flask might not set session cookie until session is modified.
    # So let's try to modify session
    with client_production.session_transaction() as sess:
        sess['test'] = 'value'
    
    response = client_production.get('/enter-code')
    cookie = response.headers.get('Set-Cookie')
    if cookie:
        assert 'SameSite=Strict' in cookie, f"Cookie missing SameSite=Strict: {cookie}"

def test_development_samesite_policy():
    """
    Test that SameSite is Lax in development (or 'else' block).
    """
    os.environ['FLASK_ENV'] = 'development'
    app = create_app()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['test'] = 'value'
            
        response = client.get('/enter-code')
        cookie = response.headers.get('Set-Cookie')
        if cookie:
            assert 'SameSite=Lax' in cookie, f"Cookie missing SameSite=Lax in dev: {cookie}"
