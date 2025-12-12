import pytest
import os
import json
import pandas as pd
from unittest.mock import MagicMock, patch
from werkzeug.datastructures import FileStorage
from app.handlers.instagram import process_instagram_file
from app.handlers.generate_synthetic_data import generate_synthetic_data

@pytest.fixture
def mock_user_temp_dir(tmp_path):
    """Mock the get_user_temp_dir to return a temporary directory."""
    with patch('app.handlers.instagram.get_user_temp_dir', return_value=str(tmp_path)):
        with patch('app.handlers.generate_synthetic_data.get_user_temp_dir', return_value=str(tmp_path)):
            yield str(tmp_path)

@pytest.fixture
def synthetic_instagram_data(mock_user_temp_dir):
    """Generate synthetic Instagram data for testing."""
    # Generate data for different categories
    files = []
    
    # 1. Liked Posts
    likes_file_path = os.path.join(mock_user_temp_dir, 'liked_posts.json')
    generate_synthetic_data('career', 'medium', likes_file_path)
    
    if os.path.exists(likes_file_path):
        with open(likes_file_path, 'rb') as f:
            content = f.read()
            files.append(FileStorage(stream=pd.io.common.BytesIO(content), filename='liked_posts.json', content_type='application/json'))

    # 2. Saved Posts
    saves_file_path = os.path.join(mock_user_temp_dir, 'saved_posts.json')
    generate_synthetic_data('foodie', 'medium', saves_file_path)
    
    if os.path.exists(saves_file_path):
        with open(saves_file_path, 'rb') as f:
            content = f.read()
            files.append(FileStorage(stream=pd.io.common.BytesIO(content), filename='saved_posts.json', content_type='application/json'))

    # 3. Videos Watched
    watches_file_path = os.path.join(mock_user_temp_dir, 'videos_watched.json')
    generate_synthetic_data('techie', 'high', watches_file_path)
    
    if os.path.exists(watches_file_path):
        with open(watches_file_path, 'rb') as f:
            content = f.read()
            files.append(FileStorage(stream=pd.io.common.BytesIO(content), filename='videos_watched.json', content_type='application/json'))
            
    return files

def test_process_instagram_file_with_synthetic_data(synthetic_instagram_data, mock_user_temp_dir):
    """Test processing of synthetically generated Instagram data."""
    
    # Mock plotting to avoid GUI issues during test
    with patch('app.handlers.instagram.plt.subplots') as mock_subplots, \
         patch('app.handlers.instagram.save_image_temp_file', return_value='mock_chart.png'), \
         patch('app.handlers.instagram.safe_save_file', return_value='mock_safe_file.csv'):
        
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_subplots.return_value = (mock_fig, mock_ax)
        
        # Call the processing function
        # process_instagram_file returns many values, let's unpack them
        df, unique_filename, insights, bump_chart, day_heatmap, month_heatmap, time_heatmap, preview_data, has_valid_data = process_instagram_file(synthetic_instagram_data)

    # Assertions
    assert has_valid_data is True
    assert not df.empty
    assert 'category' in df.columns
    assert 'timestamp' in df.columns
    
    # Verify we have data from different categories
    categories = df['category'].unique()
    assert 'Liked Media' in categories or 'Saved Media' in categories or 'Videos Watched' in categories
    
    # Verify insights extraction
    assert insights['total_entries'] == len(df)
    assert insights['unique_authors'] > 0
    
    # Verify exports
    assert unique_filename.endswith('.csv')
    assert isinstance(preview_data, dict)
    assert 'rows' in preview_data
    assert len(preview_data['rows']) > 0

def test_process_instagram_file_empty():
    """Test processing with no files."""
    files = []
    
    # Expect empty results, not an error
    df, unique_filename, insights, bump_chart, day_heatmap, month_heatmap, time_heatmap, preview_data, has_valid_data = process_instagram_file(files)
    
    assert df.empty
    assert has_valid_data is False
    assert insights == {}

def test_process_instagram_file_invalid_json(mock_user_temp_dir):
    """Test processing with an invalid JSON file."""
    bad_json = FileStorage(
        stream=pd.io.common.BytesIO(b"{invalid json"),
        filename='broken.json',
        content_type='application/json'
    )
    
    # Should handle gracefully and return empty/fail state if no other valid files
    df, unique_filename, insights, bump_chart, day_heatmap, month_heatmap, time_heatmap, preview_data, has_valid_data = process_instagram_file([bad_json])
    
    assert df.empty
    assert has_valid_data is False

