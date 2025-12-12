
import pytest
import os
import json
import pandas as pd
from unittest.mock import MagicMock, patch
from werkzeug.datastructures import FileStorage
from app.handlers.youtube import process_youtube_file
from app.handlers.generate_synthetic_data import generate_synthetic_data

@pytest.fixture
def mock_user_temp_dir(tmp_path):
    """Mock the get_user_temp_dir to return a temporary directory."""
    with patch('app.handlers.youtube.get_user_temp_dir', return_value=str(tmp_path)):
        with patch('app.handlers.generate_synthetic_data.get_user_temp_dir', return_value=str(tmp_path)):
            yield str(tmp_path)

@pytest.fixture
def synthetic_youtube_data(mock_user_temp_dir):
    """Generate synthetic YouTube data for testing."""
    files = []
    
    # Generate Watch History
    history_file_path = os.path.join(mock_user_temp_dir, 'watch-history.json')
    generate_synthetic_data('techie', 'medium', history_file_path, platform='youtube')
    
    if os.path.exists(history_file_path):
        with open(history_file_path, 'rb') as f:
            content = f.read()
            files.append(FileStorage(stream=pd.io.common.BytesIO(content), filename='watch-history.json', content_type='application/json'))

    return files

def test_process_youtube_file_with_synthetic_data(synthetic_youtube_data, mock_user_temp_dir):
    """Test processing of synthetically generated YouTube data."""
    
    # Mock plotting and file interactions
    with patch('app.handlers.youtube.plt.subplots') as mock_subplots, \
         patch('app.handlers.youtube.save_image_temp_file', return_value='mock_chart.png'), \
         patch('app.handlers.youtube.safe_save_file', return_value='mock_safe_file.csv'):
        
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_subplots.return_value = (mock_fig, mock_ax)
        
        # process_youtube_file returns: df, excel_filename, unique_filename, insights, bump_chart_name, day_heatmap_name, month_heatmap_name, time_heatmap_name, not df.empty, preview_data
        result = process_youtube_file(synthetic_youtube_data)
        
        df, excel_name, csv_name, insights, bump, day_hm, month_hm, time_hm, success, preview = result

    # Assertions
    assert success is True
    assert not df.empty
    assert 'video_title' in df.columns
    assert 'channel' in df.columns
    assert 'timestamp' in df.columns
    
    # Verify insights
    assert insights['total_videos'] == len(df)
    
    # Verify exports (mocked names)
    assert 'mock_safe_file' in csv_name
    # Excel name might come from safe_save_file return or basename logic, check mocked return usage
    
    assert isinstance(preview, dict)
    assert len(preview['rows']) > 0

def test_process_youtube_file_empty():
    """Test processing with no files."""
    files = []
    
    with pytest.raises(ValueError, match="No valid data found"):
        process_youtube_file(files)

def test_process_youtube_file_invalid_json(mock_user_temp_dir):
    """Test processing with an invalid JSON file."""
    bad_json = FileStorage(
        stream=pd.io.common.BytesIO(b"{invalid json"),
        filename='broken.json',
        content_type='application/json'
    )
    
    with pytest.raises(ValueError, match="No valid data found"):
        process_youtube_file([bad_json])
