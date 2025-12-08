import pytest
import os
import tempfile
import shutil
from app import create_app

@pytest.fixture
def client():
    """Fixture to provide a test client for the app."""
    # Set environment variables for testing
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['SECRET_KEY'] = 'test_secret_key'
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for easier testing
    
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture
def temp_test_dir():
    """Fixture to provide a temporary directory for file operations."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)
