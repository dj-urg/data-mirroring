import json
import pandas as pd
import logging
import os
import tempfile
import uuid

# Configure the logger
FLASK_ENV = os.getenv('FLASK_ENV', 'production')  # Default to 'production'

if FLASK_ENV == 'production':
    # Disable logging in production except for warnings and errors
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(levelname)s: %(message)s')
else:
    # Enable detailed logging for development
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

logger = logging.getLogger()


def process_instagram_file(files):
    """Processes multiple Instagram JSON files and merges them into one CSV."""
    try:
        all_data = []

        # Loop through each file uploaded
        for file in files:
            try:
                data = json.load(file)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON file {getattr(file, 'filename', 'unknown')}: {e}")
                continue

            # Process different sections of Instagram data
            for key, section_name in [
                ('saved_saved_media', 'Saved Media'),
                ('likes_media_likes', 'Liked Media'),
                ('impressions_history_posts_seen', 'Posts Seen'),
                ('impressions_history_chaining_seen', 'Chaining Seen'),
                ('impressions_history_videos_watched', 'Videos Watched')
            ]:
                if key in data:
                    for item in data[key]:
                        try:
                            if key == 'saved_saved_media':
                                all_data.append({
                                    'title': item.get('title', 'No Title'),
                                    'href': item['string_map_data'].get('Saved on', {}).get('href', ''),
                                    'timestamp': item['string_map_data'].get('Saved on', {}).get('timestamp', None),
                                    'category': section_name
                                })
                            elif key == 'likes_media_likes':
                                for like_data in item.get('string_list_data', []):
                                    all_data.append({
                                        'title': item.get('title', 'No Title'),
                                        'href': like_data.get('href', ''),
                                        'timestamp': like_data.get('timestamp', None),
                                        'category': section_name
                                    })
                            elif key == 'impressions_history_posts_seen':
                                all_data.append({
                                    'title': item['string_map_data'].get('Author', {}).get('value', 'Unknown'),
                                    'href': 'N/A',
                                    'timestamp': item['string_map_data'].get('Time', {}).get('timestamp', None),
                                    'category': section_name
                                })
                            elif key == 'impressions_history_chaining_seen':
                                all_data.append({
                                    'title': item['string_map_data'].get('Username', {}).get('value', 'Unknown'),
                                    'href': 'N/A',
                                    'timestamp': item['string_map_data'].get('Time', {}).get('timestamp', None),
                                    'category': section_name
                                })
                            elif key == 'impressions_history_videos_watched':
                                all_data.append({
                                    'title': item['string_map_data'].get('Author', {}).get('value', 'Unknown'),
                                    'href': 'N/A',
                                    'timestamp': item['string_map_data'].get('Time', {}).get('timestamp', None),
                                    'category': section_name
                                })
                        except KeyError as e:
                            logger.warning(f"Missing key {e} in section {section_name} for file {getattr(file, 'filename', 'unknown')}")

        if not all_data:
            logger.warning("No valid data found in the uploaded files.")
            return pd.DataFrame(), None, {}, {}, False

        # Convert to DataFrame
        df = pd.DataFrame(all_data)

        # Convert timestamps to datetime and drop invalid ones
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce').dt.date
        df = df.dropna(subset=['timestamp'])

        if df.empty:
            logger.warning("No valid timestamps found in the data.")
            return pd.DataFrame(), None, {}, {}, False

        # Extract the earliest and latest dates
        time_frame_start = df['timestamp'].min()
        time_frame_end = df['timestamp'].max()

        # Save CSV to a temporary file
        unique_filename = f"{uuid.uuid4()}.csv"
        temp_file_path = os.path.join(tempfile.gettempdir(), unique_filename)
        df.to_csv(temp_file_path, index=False)

        # Generate insights
        insights = {
            'total_entries': len(df),
            'time_frame_start': time_frame_start,
            'time_frame_end': time_frame_end
        }

        # Generate plot data
        df['year'] = pd.to_datetime(df['timestamp']).dt.year
        engagement_data = df.groupby(['year', 'title']).size().reset_index(name='engagement_count')
        top_titles_per_year = (
            engagement_data.groupby('year')
            .apply(lambda x: x.nlargest(10, 'engagement_count'))
            .reset_index(drop=True)
        )
        plot_data = {
            'years': top_titles_per_year['year'].tolist(),
            'engagement_counts': top_titles_per_year['engagement_count'].tolist(),
            'titles': top_titles_per_year['title'].tolist()
        }

        logger.info(f"Processed Instagram data with plot data: {plot_data}")

        return df, unique_filename, insights, plot_data, True

    except Exception as e:
        logger.exception(f"Error processing Instagram data: {e}")
        raise ValueError("An internal error occurred. Please try again.")
