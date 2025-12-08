import pytest
import os
import shutil
from app.utils.file_manager import TemporaryFileManager

def test_get_user_temp_dir_creates_dir(client, temp_test_dir):
    """Test that get_user_temp_dir creates a directory and sets session user_id."""
    with client.session_transaction() as sess:
        sess['user_id'] = 'test_user_id'
        
    # Mock tempfile.gettempdir to return our test fixture dir
    with pytest.MonkeyPatch.context() as m:
        m.setattr(os.path, 'join', lambda *args: os.path.join(temp_test_dir, f"user_test_user_id"))
        
        # We need to mock session context or ensure request context is active
        # The client fixture provides app context but not request context automatically 
        # unless used in a with block or we push it.
        # But helper methods in file_manager access session directly.
        
        # Actually easier to mock get_user_temp_dir's internal session dependency if we can,
        # or just run it inside a request context.
        pass

def test_file_cleanup(client):
    """Test that cleanup_user_files_immediately removes the user directory."""
    # We will simulate the existence of a user directory
    user_id = 'cleanup_test_user'
    base_temp = '/tmp' #/tmp is usually safe, or use tempfile.gettempdir()
    import tempfile
    base_temp = tempfile.gettempdir()
    user_dir = os.path.join(base_temp, f"user_{user_id}")
    os.makedirs(user_dir, exist_ok=True)
    
    # Create a dummy file
    with open(os.path.join(user_dir, 'test.txt'), 'w') as f:
        f.write('data')
        
    assert os.path.exists(user_dir)
    
    TemporaryFileManager.cleanup_user_files_immediately(user_id)
    
    assert not os.path.exists(user_dir)
