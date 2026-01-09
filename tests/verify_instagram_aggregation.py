
import pandas as pd
import unittest
from datetime import datetime

# Import the parsing logic directly to test it in isolation
# We'll mock the extraction part to simulate "parsed" data from different files
# taking the aggregation logic from `process_instagram_file` in `instagram.py`

def mock_process_instagram_data(all_data):
    """
    Simulates the aggregation logic found in process_instagram_file
    """
    if not all_data:
        return pd.DataFrame()

    df = pd.DataFrame(all_data)
    
    # Logic from instagram.py:
    # df['analysis_date'] = pd.to_datetime(df['timestamp']).dt.date
    # df = df.dropna(subset=['analysis_date'])
    # df['year'] = pd.to_datetime(df['analysis_date']).dt.year
    
    # Authors processing
    authors_df = df[df['author'] != 'Unknown']
    
    # Aggregation: Group by Year and Author
    author_data = authors_df.groupby(['year', 'author']).size().reset_index(name='engagement_count')
    
    return author_data

class TestInstagramAggregation(unittest.TestCase):
    def test_aggregation_across_files(self):
        # Scenario: Author 'ValidUser' appears in 'Liked Media' (File A) and 'Posts Seen' (File B)
        # We want to ensure the count is 2 for the year 2025.
        
        row1 = {
            'title': 'ValidUser',
            'href': 'http://example.com/1',
            'timestamp': datetime(2025, 5, 20),
            'category': 'Liked Media',
            'filename': 'liked_posts.json',
            'author': 'ValidUser',
            'year': 2025 # Pre-calculated for simple mock
        }
        
        row2 = {
            'title': 'ValidUser',
            'href': 'http://example.com/2',
            'timestamp': datetime(2025, 6, 21),
            'category': 'Posts Seen',
            'filename': 'posts_viewed.json',
            'author': 'ValidUser',
            'year': 2025
        }
        
        # Scenario: 'Unknown' author should be ignored
        row3 = {
            'title': 'Unknown',
            'href': 'http://example.com/3',
            'timestamp': datetime(2025, 1, 1),
            'category': 'Liked Media',
            'filename': 'liked_posts.json',
            'author': 'Unknown',
            'year': 2025
        }

        all_data = [row1, row2, row3]
        
        result_df = mock_process_instagram_data(all_data)
        
        print("\n--- Aggregated Data ---")
        print(result_df)
        
        # Assert 'ValidUser' has count 2
        user_row = result_df[result_df['author'] == 'ValidUser']
        self.assertFalse(user_row.empty, "ValidUser should be in the result")
        self.assertEqual(user_row.iloc[0]['engagement_count'], 2, "Count should be sum of occurrences (2)")
        
        # Assert 'Unknown' is not in the result
        unknown_row = result_df[result_df['author'] == 'Unknown']
        self.assertTrue(unknown_row.empty, "Unknown authors should be filtered out")

if __name__ == '__main__':
    unittest.main()
