import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from io import BytesIO
from werkzeug.datastructures import FileStorage
from app.handlers.netflix import process_netflix_file

def test_process_netflix_file_viewing_activity(mocker):
    """
    Test processing of Netflix ViewingActivity.csv.
    Mocks external file system calls and validates data processing.
    """
    # Mock dependencies
    mocker.patch('app.handlers.netflix.get_user_temp_dir', return_value='/tmp/mock_dir')
    mocker.patch('app.handlers.netflix.uuid.uuid4', return_value='mock-uuid')
    mocker.patch('app.handlers.netflix.safe_save_file', return_value='/tmp/mock_dir/safe_file.csv')
    mocker.patch('os.chmod')
    mocker.patch('os.remove')
    
    # Mock matplotlib plotting to avoid actual image generation
    mocker.patch('app.handlers.netflix.save_image_temp_file', return_value='mock_image.png')
    
    # Create a mock CSV file content
    csv_content = b"""Profile Name,Start Time,Duration,Attributes,Title,Supplemental Video Type,Device Type,Bookmark,Latest Bookmark,Country
User1,2023-01-01 12:00:00,00:30:00,,Movie Title,,Web Browser,00:00:00,00:30:00,US (United States)"""
    
    # Create FileStorage object to simulate file upload
    mock_file = FileStorage(
        stream=BytesIO(csv_content),
        filename='ViewingActivity.csv',
        content_type='text/csv'
    )
    
    # Call the function
    # Note: process_netflix_file expects a list of files
    df, excel_filename, unique_filename, insights, genre_treemap, day_heatmap, month_heatmap, time_heatmap, has_data, preview = process_netflix_file([mock_file])
    
    # Assertions
    assert has_data is True
    assert len(df) == 1
    assert df.iloc[0]['title'] == 'Movie Title'
    assert df.iloc[0]['country'] == 'US'
    assert insights['unique_titles'] == 1
    assert unique_filename == 'safe_file.csv'
    assert excel_filename == 'safe_file.csv'  # Based on mock behavior likely, or just basename
    
    # Verify plotting functions were called (implicitly via save_image_temp_file calls)
    # Since we mocked save_image_temp_file, we assume the generator functions were called.
    # We could also mock the generator functions to verify directly.

def test_process_netflix_file_no_data(mocker):
    """Test processing with no valid data raises ValueError."""
    # Mock empty file list
    with pytest.raises(ValueError, match="No valid data found"):
        process_netflix_file([])
