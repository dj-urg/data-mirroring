
import pytest
import os
import json
import pandas as pd
from unittest.mock import MagicMock, patch
from werkzeug.datastructures import FileStorage
from app.handlers.tiktok import process_tiktok_file
from app.handlers.generate_synthetic_data import generate_synthetic_data

@pytest.fixture
def mock_user_temp_dir(tmp_path):
    """Mock the get_user_temp_dir to return a temporary directory."""
    with patch('app.handlers.tiktok.get_user_temp_dir', return_value=str(tmp_path)):
        with patch('app.handlers.generate_synthetic_data.get_user_temp_dir', return_value=str(tmp_path)):
            yield str(tmp_path)

@pytest.fixture
def synthetic_tiktok_data(mock_user_temp_dir):
    """Generate synthetic TikTok data for testing."""
    files = []
    
    # Generate User Data
    data_file_path = os.path.join(mock_user_temp_dir, 'user_data.json')
    generate_synthetic_data('fitness', 'high', data_file_path, platform='tiktok')
    
    if os.path.exists(data_file_path):
        with open(data_file_path, 'rb') as f:
            content = f.read()
            files.append(FileStorage(stream=pd.io.common.BytesIO(content), filename='user_data.json', content_type='application/json'))

    return files

def test_process_tiktok_file_with_synthetic_data(synthetic_tiktok_data, mock_user_temp_dir):
    """Test processing of synthetically generated TikTok data."""
    
    # Mock plotting and file interactions
    with patch('app.handlers.tiktok.plt.subplots') as mock_subplots, \
         patch('app.handlers.tiktok.save_image_temp_file', return_value='mock_chart.png'), \
         patch('app.handlers.tiktok.safe_save_file', return_value='mock_safe_file.csv'):
        
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_subplots.return_value = (mock_fig, mock_ax)
        
        # process_tiktok_file returns: df, csv_name, excel_name, url_name, insights, day_heatmap, time_heatmap, month_heatmap, success, preview
        result = process_tiktok_file(synthetic_tiktok_data)
        
        df, csv_name, excel_name, url_name, insights, day_hm, time_hm, month_hm, success, preview = result

    # Assertions
    assert success is True
    assert not df.empty
    assert 'video_title' in df.columns
    assert 'source' in df.columns
    assert 'timestamp' in df.columns
    
    # Verify insights
    assert insights['total_videos'] == len(df)
    
    # Verify exports (mocked names)
    assert 'mock_safe_file' in csv_name
    
    assert isinstance(preview, dict)
    assert len(preview['rows']) > 0

def test_process_tiktok_file_empty():
    """Test processing with no files."""
    files = []
    
    with pytest.raises(ValueError, match="No valid video data found"):
        process_tiktok_file(files)

def test_process_tiktok_file_invalid_json(mock_user_temp_dir):
    """Test processing with an invalid JSON file."""
    bad_json = FileStorage(
        stream=pd.io.common.BytesIO(b"{invalid json"),
        filename='broken.json',
        content_type='application/json'
    )
    
    # Note: The handler logs error but might raise ValueError from parse_json_file check or subsequent logic
    with pytest.raises(ValueError):
        process_tiktok_file([bad_json])
