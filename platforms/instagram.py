import json
import pandas as pd
import logging
import os
import time

# Configure the logger
FLASK_ENV = os.getenv('FLASK_ENV', 'development')

if FLASK_ENV == 'production':
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(levelname)s: %(message)s')
else:
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger()

BASE_DIR = os.getenv('APP_BASE_DIR', os.path.dirname(os.path.abspath(__file__)))

# Use a writable directory within your project folder
download_dir = os.path.join(BASE_DIR, 'downloads')  # Change to a writable path
upload_dir = os.path.join(BASE_DIR, 'uploads')  # Change to a writable path

os.makedirs(download_dir, exist_ok=True)
os.makedirs(upload_dir, exist_ok=True)

def process_instagram_file(files):
    """Processes multiple Instagram JSON files and merges them into one CSV."""
    try:
        all_data = []
        
        # Loop through each file uploaded
        for file in files:
            data = json.load(file)
            flat_instagram_data = []

            # Process different sections of Instagram data
            for key in ['saved_saved_media', 'likes_media_likes', 'impressions_history_posts_seen', 
                        'impressions_history_chaining_seen', 'impressions_history_videos_watched']:
                
                if key in data:
                    for item in data[key]:
                        if key == 'saved_saved_media':
                            flat_instagram_data.append({
                                'title': item.get('title', 'No Title'),
                                'href': item['string_map_data'].get('Saved on', {}).get('href', ''),
                                'timestamp': pd.to_datetime(item['string_map_data'].get('Saved on', {}).get('timestamp', 0), unit='s'),
                                'category': key
                            })
                        elif key == 'likes_media_likes':
                            for like_data in item.get('string_list_data', []):
                                flat_instagram_data.append({
                                    'title': item.get('title', 'No Title'),
                                    'href': like_data.get('href', ''),
                                    'timestamp': pd.to_datetime(like_data.get('timestamp', 0), unit='s'),
                                    'category': key
                                })
                        elif key == 'impressions_history_posts_seen':
                            flat_instagram_data.append({
                                'title': item['string_map_data'].get('Author', {}).get('value', 'Unknown'),
                                'href': 'N/A',
                                'timestamp': pd.to_datetime(item['string_map_data'].get('Time', {}).get('timestamp', 0), unit='s'),
                                'category': key
                            })
                        elif key == 'impressions_history_chaining_seen':
                            flat_instagram_data.append({
                                'title': item['string_map_data'].get('Username', {}).get('value', 'Unknown'),
                                'href': 'N/A',
                                'timestamp': pd.to_datetime(item['string_map_data'].get('Time', {}).get('timestamp', 0), unit='s'),
                                'category': key
                            })
                        elif key == 'impressions_history_videos_watched':
                            flat_instagram_data.append({
                                'title': item['string_map_data'].get('Author', {}).get('value', 'Unknown'),
                                'href': 'N/A',
                                'timestamp': pd.to_datetime(item['string_map_data'].get('Time', {}).get('timestamp', 0), unit='s'),
                                'category': key
                            })

            all_data.extend(flat_instagram_data)

        # Convert to DataFrame
        df = pd.DataFrame(all_data)

        # Format the 'timestamp' column to only include date (YYYY-MM-DD)
        df['timestamp'] = df['timestamp'].dt.date

        # Drop rows where timestamp is NaT (invalid dates)
        valid_timestamps = df['timestamp'].dropna()

        # If valid timestamps exist, get the earliest and latest dates
        if not valid_timestamps.empty:
            time_frame_start = valid_timestamps.min()  # Already in date format
            time_frame_end = valid_timestamps.max()  # Already in date format
        else:
            time_frame_start, time_frame_end = 'N/A', 'N/A'
        
        # Save to CSV (with the timestamp formatted as date)
        csv_file_path = 'output_instagram.csv'
        full_csv_path = os.path.join(download_dir, 'output_instagram.csv')
        df.to_csv(full_csv_path, index=False)
        time.sleep(1)

        # Generate insights
        insights = {
            'total_entries': len(df),
            'time_frame_start': time_frame_start,
            'time_frame_end': time_frame_end
        }

        # Extract the year from the timestamp
        df['year'] = pd.to_datetime(df['timestamp']).dt.year

        # Group by year and title, and count the occurrences per year
        engagement_data = df.groupby(['year', 'title']).size().reset_index(name='engagement_count')

        # For each year, select the top 10 most frequent titles
        top_titles_per_year = engagement_data.groupby('year').apply(lambda x: x.nlargest(10, 'engagement_count')).reset_index(drop=True)

        # Prepare data for visualization
        plot_data = {
            'years': top_titles_per_year['year'].tolist(),
            'engagement_counts': top_titles_per_year['engagement_count'].tolist(),
            'titles': top_titles_per_year['title'].tolist()
        }

        logger.info(f"Processed Instagram data with plot data: {plot_data}")

        # Return the DataFrame, CSV file path, insights, and plot data
        return df, csv_file_path, insights, plot_data

    except Exception as e:
        logger.error(f"Error processing Instagram data: {e}")
        raise ValueError(f"Error processing Instagram data: {e}")