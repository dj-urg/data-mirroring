import os
import tempfile
from flask import session

def get_user_temp_dir():
    """Create and return a user-specific temporary directory for the current session."""
    user_session_id = session.get('user_id')

    if not user_session_id:
        user_session_id = os.urandom(16).hex()  # Generate a random session ID
        session['user_id'] = user_session_id  # Store in session

    user_temp_dir = os.path.join(tempfile.gettempdir(), f"user_{user_session_id}")

    os.makedirs(user_temp_dir, exist_ok=True)  # Ensure the directory exists
    return user_temp_dir