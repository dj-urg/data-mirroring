
import unittest
import sys
import os
import pandas as pd
from datetime import datetime

# Adjust path to import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from app.handlers.instagram import parse_instagram_item

class TestInstagramParsing(unittest.TestCase):
    def test_parse_suggested_profiles_map_data(self):
        # Scenario: Suggested Profiles with string_map_data (Common structure)
        item = {
            "string_map_data": {
                "Username": {"value": "suggested_user_1"},
                "Time": {"timestamp": 1704067200} # 2024-01-01
            }
        }
        result = parse_instagram_item(item, 'Suggested Profiles', 'suggested_profiles_viewed.json')
        self.assertIsNotNone(result)
        self.assertEqual(result['author'], 'suggested_user_1')
        self.assertEqual(result['category'], 'Suggested Profiles')
        # Check timestamp year
        self.assertEqual(result['timestamp'].year, 2024)

    def test_parse_suggested_profiles_list_data(self):
        # Scenario: Suggested Profiles with string_list_data (Alternative structure)
        item = {
            "title": "suggested_user_2",
            "string_list_data": [{
                "timestamp": 1704153600, # 2024-01-02
                "href": "http://instagram.com/user2"
            }]
        }
        result = parse_instagram_item(item, 'Suggested Profiles', 'suggested_profiles_viewed.json')
        self.assertIsNotNone(result)
        self.assertEqual(result['author'], 'suggested_user_2')
        self.assertEqual(result['timestamp'].year, 2024)

    def test_parse_posts_seen(self):
        # Scenario: Posts Seen
        item = {
            "string_map_data": {
                "Author": {"value": "post_author"},
                "Time": {"timestamp": 1704240000} # 2024-01-03
            }
        }
        result = parse_instagram_item(item, 'Posts Seen', 'posts_viewed.json')
        self.assertEqual(result['author'], 'post_author')

if __name__ == '__main__':
    unittest.main()
