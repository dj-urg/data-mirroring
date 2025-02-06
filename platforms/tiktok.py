import json
import pandas as pd
import os
import tempfile
import uuid
import logging
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import traceback
import re

# Use 'Agg' backend for headless image generation
matplotlib.use('Agg')

# Configure the logger
FLASK_ENV = os.getenv('FLASK_ENV', 'production')

if FLASK_ENV == 'production':
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(levelname)s: %(message)s')
else:
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

logger = logging.getLogger()

# Helper function to save images as a temporary file
def save_image_temp_file(fig):
    """Saves an image as a temporary file and returns the filename."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
        fig.savefig(tmp_file.name, bbox_inches='tight')
        plt.close(fig)  # Free up memory
        return os.path.basename(tmp_file.name)

# Helper function to save CSV as a temporary file
def save_csv_temp_file(df):
    """Saves CSV data as a temporary file and returns the filename."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
        df.to_csv(tmp_file.name, index=False)
        os.chmod(tmp_file.name, 0o600)  # Secure file permissions
        return os.path.basename(tmp_file.name)

# Generate a bump chart similar to YouTube's
def generate_custom_bump_chart(source_ranking):
    fig, ax = plt.subplots(figsize=(8, 3))

    sources = source_ranking['source'].unique()
    years = sorted(source_ranking['year'].unique())

    for source in sources:
        source_data = source_ranking[source_ranking['source'] == source]
        year_values = [years.index(year) for year in source_data['year']]
        rank_values = source_data['rank'].values

        ax.plot(year_values, -rank_values, marker='o', label=source)

    ax.set_xticks(range(len(years)))
    ax.set_xticklabels(years)
    ax.set_yticks([])  # Hide y-axis ticks
    ax.legend()
    
    plt.tight_layout()
    return fig

# Generate heatmap for TikTok activity
def generate_heatmap(hourly_counts):
    fig, ax = plt.subplots(figsize=(8, 2))
    hourly_df = pd.DataFrame({'Hour': hourly_counts.index, 'Count': hourly_counts.values}).set_index('Hour')
    sns.heatmap(hourly_df.T, annot=True, fmt="d", cmap="Blues", ax=ax, cbar=False)
    ax.set_xlabel("Hour of the Day")
    plt.tight_layout()
    return fig

# Main processing function for TikTok files
def process_tiktok_file(files):
    try:
        all_data = []

        for file in files:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                logger.error("Uploaded file is not valid JSON.")
                raise ValueError("Invalid JSON file. Please upload a valid TikTok data file.")

            activity_data = data.get('Activity', {})

            # Process Favorite Videos
            fav_videos = activity_data.get('Favorite Videos', {}).get('FavoriteVideoList', [])
            if not isinstance(fav_videos, list):
                logger.warning("Unexpected format in 'Favorite Videos'. Expected a list.")
                fav_videos = []

            for item in fav_videos:
                timestamp = pd.to_datetime(item.get('Date', ''), errors='coerce')
                all_data.append({
                    'video_title': 'Favorite Video',
                    'video_url': item.get('Link', ''),
                    'timestamp': timestamp,
                    'source': 'Favorite Videos'
                })

            # Process Like List
            liked_videos = activity_data.get('Like List', {}).get('ItemFavoriteList', [])
            if not isinstance(liked_videos, list):
                logger.warning("Unexpected format in 'Like List'. Expected a list.")
                liked_videos = []

            for item in liked_videos:
                timestamp = pd.to_datetime(item.get('Date', ''), errors='coerce')
                all_data.append({
                    'video_title': 'Liked Video',
                    'video_url': item.get('Link', ''),
                    'timestamp': timestamp,
                    'source': 'Like List'
                })

        if not all_data:
            logger.error("No valid video data found in the uploaded files.")
            raise ValueError("No valid video data found in the uploaded files.")

        df = pd.DataFrame(all_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        insights = {
            'total_videos': len(df),
            'time_frame_start': df['timestamp'].min().date() if not df.empty else 'N/A',
            'time_frame_end': df['timestamp'].max().date() if not df.empty else 'N/A'
        }

        df['year'] = df['timestamp'].dt.year
        df['hour'] = df['timestamp'].dt.hour
        activity_counts = df['hour'].value_counts().sort_index()

        # Prepare visualization
        source_data = df.groupby(['year', 'source']).size().reset_index(name='view_counts')
        top_sources_per_year = source_data.groupby('year').apply(lambda x: x.nlargest(5, 'view_counts')).reset_index(drop=True)
        top_sources_per_year['rank'] = top_sources_per_year.groupby('year')['view_counts'].rank(ascending=False, method='first')

        bump_chart_name = save_image_temp_file(generate_custom_bump_chart(top_sources_per_year))
        heatmap_name = save_image_temp_file(generate_heatmap(activity_counts))
        csv_file_name = save_csv_temp_file(df)
        
        # Generate HTML preview from DataFrame
        raw_html = df.head(5).to_html(
            classes="table table-striped text-right",
            index=False,
            escape=False,
            render_links=True,
            border=0
        )

        # Remove all inline styles (especially `style="text-align: right;"`)
        csv_preview_html = re.sub(r'style="[^"]*"', '', raw_html)

        return df, csv_file_name, insights, bump_chart_name, heatmap_name, not df.empty, csv_preview_html

    except Exception as e:
        logger.error(f"Error processing TikTok file: {type(e).__name__} - {str(e)}")
        logger.error(traceback.format_exc())  # This will print the full traceback
        raise ValueError(f"Error processing TikTok data: {str(e)}")