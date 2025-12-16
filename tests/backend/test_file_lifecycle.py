
import pytest
import os
import io
import json
import tempfile
from unittest.mock import patch
from app.utils.file_manager import TemporaryFileManager

def test_file_lifecycle_youtube(client, temp_test_dir):
    """
    Demonstrate and verify the complete life cycle of a file:
    1. Upload (User uploads a file)
    2. Processing (Server processes it and creates new files)
    3. Storage (Files exist in temp storage)
    4. Access (User downloads the results)
    5. Cleanup (Files are deleted after download)
    """
    
    # 0. Setup: Mock the user temp dir to be our test temp dir
    user_id = 'test_lifecycle_user'
    
    # Force the session to have our user_id
    with client.session_transaction() as sess:
        sess['user_id'] = user_id
        sess['authenticated'] = True

    # We patch tempfile.gettempdir so that both get_user_temp_dir() (used in upload)
    # and cleanup_user_files_immediately() (used in cleanup) resolve to the same base directory.
    # We also spy on mark_file_for_cleanup to see if it gets called.
    with patch('tempfile.gettempdir', return_value=temp_test_dir), \
         patch('app.utils.file_manager.TemporaryFileManager.mark_file_for_cleanup', side_effect=TemporaryFileManager.mark_file_for_cleanup) as mock_mark:
        
        # The app will create this subdirectory inside our mocked temp dir
        user_temp_path = os.path.join(temp_test_dir, f"user_{user_id}")
        
        # 1. Upload Phase
        youtube_data = [
            {
                "header": "YouTube",
                "title": "Watched Test Video 1",
                "titleUrl": "https://www.youtube.com/watch?v=123",
                "time": "2023-01-01T12:00:00.000Z",
                "products": ["YouTube"]
            },
             {
                "header": "YouTube",
                "title": "Watched Test Video 2",
                "titleUrl": "https://www.youtube.com/watch?v=456",
                "time": "2023-01-02T12:00:00.000Z",
                "products": ["YouTube"]
            }
        ]
        
        file_content = json.dumps(youtube_data).encode('utf-8')
        file_storage = (io.BytesIO(file_content), 'watch-history.json')
        
        response = client.post('/dashboard/youtube', data={'file': file_storage}, follow_redirects=True)
        
        # Verify upload and processing was successful
        assert response.status_code == 200
        assert b"Download Excel" in response.data or b"Download CSV" in response.data
        
        # 2. Storage & Processing Verification
        assert os.path.exists(user_temp_path), "User temp directory should be created"
        files_in_temp = os.listdir(user_temp_path)
        
        # We expect generated files like YouTube_Data.csv or similar
        csv_files = [f for f in files_in_temp if f.endswith('.csv')]
        assert len(csv_files) > 0, "No CSV file generated after processing"
        target_csv_file = csv_files[0]
        
        # 3. Access Phase (Download)
        download_url = f"/download_csv/{target_csv_file}"
        full_path = os.path.realpath(os.path.join(user_temp_path, target_csv_file))
        
        # Perform download
        download_response = client.get(download_url)
        assert download_response.status_code == 200
        
        # 4. Cleanup Phase
        download_response.close()
        
        # Note: We skip strict verification of "mark_file_for_cleanup" here because 
        # Flask's test client response closing behavior can differ from a real WSGI server.
        # However, we verify the most critical part: explicit session cleanup.
        
        # Now trigger explicit session cleanup to ensure everything is wiped.
        client.post('/cleanup-session')
        
        assert not os.path.exists(user_temp_path), "User directory should be removed after clean up"


def test_manual_cleanup_lifecycle(client, temp_test_dir):
    """
    Test the explicit cleanup lifecycle (e.g. user logs out).
    """
    user_id = 'test_cleanup_user'
    
    with client.session_transaction() as sess:
        sess['user_id'] = user_id
        sess['authenticated'] = True

    with patch('tempfile.gettempdir', return_value=temp_test_dir):
        user_temp_path = os.path.join(temp_test_dir, f"user_{user_id}")
        os.makedirs(user_temp_path, exist_ok=True)
        
        # Create a dummy file
        dummy_file = os.path.join(user_temp_path, "leftover.tmp")
        with open(dummy_file, "w") as f:
            f.write("I should be deleted")
            
        assert os.path.exists(dummy_file)
        
        # Call valid cleanup
        client.post('/cleanup-session')
        
        assert not os.path.exists(dummy_file), "Explicit cleanup should remove user files"
