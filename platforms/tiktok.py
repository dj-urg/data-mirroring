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

def process_tiktok_file(files):
    """Processes multiple TikTok JSON data files and merges them into a single DataFrame."""
    try:
        all_data = []
        
        # Loop through each file in the files list
        for file in files:
            data = json.load(file)
            flattened_data = []

            # Extract data from 'Favorite Videos'
            if 'Favorite Videos' in data['Activity']:
                for item in data['Activity']['Favorite Videos'].get('FavoriteVideoList', []):
                    timestamp = pd.to_datetime(item.get('Date', ''), errors='coerce')  # Coerce invalid formats to NaT
                    flattened_data.append({
                        'video_title': 'Favorite Video',
                        'video_url': item.get('Link', ''),
                        'timestamp': timestamp,
                        'source': 'Favorite Videos'
                    })

            # Extract data from 'Like List'
            if 'Like List' in data['Activity']:
                for item in data['Activity']['Like List'].get('ItemFavoriteList', []):
                    timestamp = pd.to_datetime(item.get('Date', ''), errors='coerce')  # Coerce invalid formats to NaT
                    flattened_data.append({
                        'video_title': 'Liked Video',
                        'video_url': item.get('Link', ''),
                        'timestamp': timestamp,
                        'source': 'Like List'
                    })

            all_data.extend(flattened_data)

        # Convert to DataFrame
        df = pd.DataFrame(all_data)

        # Ensure the 'timestamp' is properly parsed as a datetime object
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Drop rows where timestamp is NaT (invalid dates)
        valid_timestamps = df['timestamp'].dropna()

        # If valid timestamps exist, get the earliest and latest dates
        if not valid_timestamps.empty:
            time_frame_start = valid_timestamps.min().date()  # Convert to date for readability
            time_frame_end = valid_timestamps.max().date()
        else:
            time_frame_start, time_frame_end = 'N/A', 'N/A'
        
        # Generate a unique filename using UUID and save CSV to a temporary file
        unique_filename = f"{uuid.uuid4()}.csv"
        temp_file_path = os.path.join(tempfile.gettempdir(), unique_filename)
        df.to_csv(temp_file_path, index=False)

        logger.info(f"CSV file saved successfully at: {temp_file_path}")

        # Generate insights
        insights = {
            'total_videos': len(df),
            'time_frame_start': time_frame_start,
            'time_frame_end': time_frame_end
        }

        # Extract the year from the timestamp for grouping
        df['year'] = df['timestamp'].dt.year

        # Group by year and source, and count the occurrences of each source per year
        source_data = df.groupby(['year', 'source']).size().reset_index(name='view_counts')

        # For each year, select the top sources
        top_sources_per_year = source_data.groupby('year').apply(lambda x: x.nlargest(10, 'view_counts')).reset_index(drop=True)

        # Prepare data for visualization (Bar Chart)
        plot_data = {
            'years': top_sources_per_year['year'].tolist(),
            'view_counts': top_sources_per_year['view_counts'].tolist(),
            'sources': top_sources_per_year['source'].tolist()
        }

        # Check if plot data has any missing values
        if not plot_data['years'] or not plot_data['view_counts'] or not plot_data['sources']:
            logger.error("Plot data contains incomplete values.")
            plot_data = {}  # Reset plot_data if it's malformed

        has_valid_data = not df.empty

        # Extract hour for time of day analysis
        df['hour'] = df['timestamp'].dt.hour
        activity_counts = df['hour'].value_counts().sort_index()

        # Time of day insights
        morning = activity_counts[(activity_counts.index >= 6) & (activity_counts.index < 12)].sum()
        afternoon = activity_counts[(activity_counts.index >= 12) & (activity_counts.index < 18)].sum()
        evening = activity_counts[(activity_counts.index >= 18) & (activity_counts.index < 24)].sum()
        night = activity_counts[(activity_counts.index >= 0) & (activity_counts.index < 6)].sum()

        insights['morning_activity'] = morning
        insights['afternoon_activity'] = afternoon
        insights['evening_activity'] = evening
        insights['night_activity'] = night

        # Optionally: Prepare heatmap data for visualization (if desired)
        heatmap_data = {
            'hours': list(activity_counts.index),
            'activity_counts': list(activity_counts.values)
        }

        # Return DataFrame, filename, insights, plot data, and heatmap data
        return df, unique_filename, insights, plot_data, heatmap_data, has_valid_data

    except Exception as e:
        logger.warning(f"Error occurred: {type(e).__name__} - {str(e)}")  # Avoid logging sensitive data
        raise ValueError("An internal error occurred. Please try again.")