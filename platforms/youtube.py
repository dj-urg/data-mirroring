import json
import pandas as pd
import logging
import os
import tempfile

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

def process_youtube_file(files):
    """Processes multiple YouTube JSON data files and returns insights and plot data."""
    try:
        all_data = []

        for file in files:
            data = json.load(file)
            flattened_data = []

            for item in data:
                subtitles = item.get('subtitles', [{}])
                subtitle_name = subtitles[0].get('name', 'Unknown') if subtitles else 'Unknown'
                subtitle_url = subtitles[0].get('url', '') if subtitles else ''
                timestamp = pd.to_datetime(item.get('time', ''), errors='coerce')

                flattened_data.append({
                    'video_title': item.get('title', 'No Title'),
                    'video_url': item.get('titleUrl', ''),
                    'timestamp': timestamp,
                    'channel': subtitle_name,
                    'channel_url': subtitle_url
                })

            all_data.extend(flattened_data)

        df = pd.DataFrame(all_data)
        df['timestamp'] = df['timestamp'].dt.date
        valid_timestamps = df['timestamp'].dropna()

        if not valid_timestamps.empty:
            time_frame_start = valid_timestamps.min()
            time_frame_end = valid_timestamps.max()
        else:
            time_frame_start, time_frame_end = 'N/A', 'N/A'

        insights = {
            'total_videos': len(df),
            'time_frame_start': time_frame_start,
            'time_frame_end': time_frame_end
        }

        # Prepare data for visualization
        df['year'] = pd.to_datetime(df['timestamp']).dt.year
        channel_data = df.groupby(['year', 'channel']).size().reset_index(name='view_counts')
        top_channels_per_year = channel_data.groupby('year').apply(lambda x: x.nlargest(10, 'view_counts')).reset_index(drop=True)

        plot_data = {
            'years': top_channels_per_year['year'].tolist(),
            'view_counts': top_channels_per_year['view_counts'].tolist(),
            'channels': top_channels_per_year['channel'].tolist()
        }

        has_valid_data = not df.empty

        # Save the CSV content to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
            df.to_csv(tmp_file.name, index=False)  # Save DataFrame directly to the temp file
            temp_file_path = tmp_file.name  # Store the path for later use

        # Return the DataFrame, temporary file path, insights, and plot data
        return df, temp_file_path, insights, plot_data, has_valid_data

    except Exception as e:
        logger.error(f"Error processing YouTube data: {type(e).__name__} - {str(e)}")
        raise ValueError(f"Error processing YouTube data: {type(e).__name__} - Check logs for details")