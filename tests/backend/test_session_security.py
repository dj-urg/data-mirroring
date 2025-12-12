import pytest
from flask import session
from werkzeug.security import generate_password_hash
import os

def test_user_id_set_on_login(client, mocker):
    """Test that session['user_id'] is explicitly set upon successful login."""
    
    # Mock authentication setup
    password = "correct_password"
    hashed_password = generate_password_hash(password)
    mocker.patch.dict('os.environ', {'ACCESS_CODE_HASH': hashed_password})
    
    # Perform login
    response = client.post('/enter-code', data={'code': password}, follow_redirects=True)
    
    # Check successful login
    assert response.status_code == 200
    
    # Verify user_id is in session and is a non-empty string
    with client.session_transaction() as sess:
        assert sess.get('authenticated') is True
        assert 'user_id' in sess
        assert sess['user_id'] is not None
        assert isinstance(sess['user_id'], str)
        assert len(sess['user_id']) > 0
        print(f"Verified Session User ID: {sess['user_id']}")

def test_user_id_regenerated_on_new_login(client, mocker):
    """Test that a new user_id is generated for a new login session."""
    
    # Mock authentication setup
    password = "correct_password"
    hashed_password = generate_password_hash(password)
    mocker.patch.dict('os.environ', {'ACCESS_CODE_HASH': hashed_password})
    
    # First Login
    client.post('/enter-code', data={'code': password}, follow_redirects=True)
    with client.session_transaction() as sess:
        first_user_id = sess.get('user_id')
        
    # Logout
    client.get('/logout', follow_redirects=True)
    
    # Second Login
    client.post('/enter-code', data={'code': password}, follow_redirects=True)
    with client.session_transaction() as sess:
        second_user_id = sess.get('user_id')
        
    assert first_user_id != second_user_id

def test_session_tampering_fails(client, mocker):
    """Test that modifying the session cookie invalidates it (due to cryptographic signing)."""
    
    # Mock authentication
    password = "correct_password"
    hashed_password = generate_password_hash(password)
    mocker.patch.dict('os.environ', {'ACCESS_CODE_HASH': hashed_password})
    
    # Login to get a valid cookie
    response = client.post('/enter-code', data={'code': password}, follow_redirects=True)
    assert response.status_code == 200
    
    # Extract the session cookie value from headers
    cookie_header = response.headers.get('Set-Cookie')
    assert cookie_header is not None, "No Set-Cookie header found"
    
    # Parse the session cookie value
    import re
    match = re.search(r'session=([^;]+)', cookie_header)
    assert match is not None, "Session cookie not found in headers"
    original_value = match.group(1)
    parts = original_value.split('.')
    if len(parts) >= 1:
        # Just appending 'junk' to the first part (payload)
        parts[0] = parts[0] + 'junk'
        tampered_value = '.'.join(parts)
        
        # Set the tampered cookie
        client.set_cookie(domain='localhost', key='session', value=tampered_value)
        
        # Try to access a protected route
        response = client.get('/platform-selection', follow_redirects=True)
        
        # Should be redirected to login (enter-code) because session is invalid
        # Note: In our app, invalid session -> redirect to /enter-code
        assert '/enter-code' in response.request.url
        assert "Invalid access code" not in response.get_data(as_text=True) # Just a cohesive redirect

