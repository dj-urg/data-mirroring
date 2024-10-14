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

def process_youtube_file(files):
    """Processes multiple YouTube JSON data files and merges them into a single DataFrame."""
    try:
        # Initialize an empty list to hold data from all files
        all_data = []
        
        # Loop through each file in the files list
        for file in files:
            # Read the file content
            data = json.load(file)
            flattened_data = []

            # Flatten the data structure and extract relevant fields
            for item in data:
                subtitles = item.get('subtitles', [{}])
                subtitle_name = subtitles[0].get('name', 'Unknown') if subtitles else 'Unknown'
                subtitle_url = subtitles[0].get('url', '') if subtitles else ''
                
                # Convert timestamp using pd.to_datetime
                timestamp = pd.to_datetime(item.get('time', ''), errors='coerce')  # Coerce invalid formats to NaT
                
                flattened_data.append({
                    'video_title': item.get('title', 'No Title'),
                    'video_url': item.get('titleUrl', ''),
                    'timestamp': timestamp,
                    'channel': subtitle_name,
                    'channel_url': subtitle_url
                })

            # Append the data to the all_data list
            all_data.extend(flattened_data)

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
        csv_file_path = 'output_youtube.csv'
        full_csv_path = os.path.join(download_dir, 'output_youtube.csv')
        df.to_csv(full_csv_path, index=False)
        time.sleep(1)

        # Log after saving the file
        if os.path.exists(full_csv_path):
            logger.info(f"CSV file saved successfully at: {full_csv_path}")
        else:
            logger.error(f"Failed to save CSV file at: {full_csv_path}")

        # Generate insights
        insights = {
            'total_videos': len(df),
            'time_frame_start': time_frame_start,
            'time_frame_end': time_frame_end
        }

        # Extract the year from the timestamp
        df['year'] = pd.to_datetime(df['timestamp']).dt.year

        # Group by year and channel, and count the occurrences of each channel per year
        channel_data = df.groupby(['year', 'channel']).size().reset_index(name='view_counts')

        # For each year, select the top 10 most frequent channels
        top_channels_per_year = channel_data.groupby('year').apply(lambda x: x.nlargest(10, 'view_counts')).reset_index(drop=True)

        # Prepare data for visualization
        plot_data = {
            'years': top_channels_per_year['year'].tolist(),
            'view_counts': top_channels_per_year['view_counts'].tolist(),
            'channels': top_channels_per_year['channel'].tolist()
        }

        # Ensure there are no None values in plot_data
        if not plot_data['years'] or not plot_data['view_counts'] or not plot_data['channels']:
            logger.error("Plot data contains incomplete values.")
            plot_data = {}  # Reset plot_data if it's malformed

        has_valid_data = not df.empty
        # Return the DataFrame, CSV file path, insights, and plot data
        return df, csv_file_path, insights, plot_data, has_valid_data

    except Exception as e:
            # Only log the type of the error without any data content
            logger.error(f"Error processing YouTube data: {type(e).__name__} - {str(e)}")
            raise ValueError(f"Error processing YouTube data: {type(e).__name__} - Check logs for details")