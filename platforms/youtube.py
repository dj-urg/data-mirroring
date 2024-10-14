import json
import pandas as pd
import os
import tempfile
import uuid

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

        # Generate insights
        insights = {
            'total_videos': len(df),
            'time_frame_start': df['timestamp'].min(),
            'time_frame_end': df['timestamp'].max(),
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

        # Generate a unique filename using UUID and save CSV to temporary file
        unique_filename = f"{uuid.uuid4()}.csv"
        temp_file_path = os.path.join(tempfile.gettempdir(), unique_filename)
        df.to_csv(temp_file_path, index=False)

        return df, unique_filename, insights, plot_data, not df.empty

    except Exception as e:
        raise ValueError(f"Error processing YouTube data: {type(e).__name__} - {str(e)}")