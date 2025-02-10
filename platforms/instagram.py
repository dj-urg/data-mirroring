import json
import pandas as pd
import os
import tempfile
import uuid
import logging
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.lines import Line2D
from app.utils.file_utils import get_user_temp_dir

# Use 'Agg' backend to avoid GUI issues
matplotlib.use('Agg')

# Configure the logger
FLASK_ENV = os.getenv('FLASK_ENV', 'production')
logging_level = logging.DEBUG if FLASK_ENV == 'development' else logging.WARNING
logging.basicConfig(level=logging_level, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger()

# Custom visualization functions
def add_line(ax, year_values, rank_values, linewidth=3, color="black"):
    ax.add_artist(Line2D(year_values, -rank_values, linewidth=linewidth, color=color))

def add_circle(ax, year_value, rank_value, marker_size=15, color="black"):
    ax.plot(year_value, -rank_value, 'o', color=color, markersize=marker_size)

def add_text(ax, year_value, rank_value, text, offset=0.02):
    ax.text(year_value + offset, -rank_value, text, fontsize=10, va='bottom', ha='left')

def format_ticks(ax, years):
    ax.set(xlim=(-0.5, len(years) - 0.5), ylim=(-5.5, -0.5))
    ax.set_xticks(ticks=range(len(years)), labels=years)
    ax.set_yticks([])
    ax.tick_params("x", labeltop=True, bottom=False, labelsize=12, pad=4)

def save_image_temp_file(fig):
    """Saves an image as a temporary file and returns the filename."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
        fig.savefig(tmp_file.name, bbox_inches='tight')
        return os.path.basename(tmp_file.name)

def generate_custom_bump_chart(df):
    """Generates a bump chart for Instagram engagement per year."""
    years = sorted(df['year'].unique())
    fig, ax = plt.subplots(figsize=(8, 3))
    format_ticks(ax, years)

    colors = plt.get_cmap("tab10").colors
    for i, category in enumerate(df['category'].unique()):
        category_data = df[df['category'] == category]
        year_values = [years.index(year) for year in category_data['year']]
        rank_values = category_data['rank'].values
        color = colors[i % len(colors)]

        add_line(ax, year_values, rank_values, color=color)
        for j, year in enumerate(year_values):
            add_circle(ax, year, rank_values[j], color=color)
        add_text(ax, year_values[-1], rank_values[-1], category)

    plt.tight_layout()
    return fig  # Return the figure itself, not the filename

def generate_heatmap(df):
    """Generates a heatmap showing Instagram engagement by day of the week."""
    if 'timestamp' not in df.columns:
        logger.warning("Timestamp column not found in the DataFrame.")
        return None  # Or raise an exception, based on your preference

    # Prepare the data
    df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.day_name()
    day_counts = df['day_of_week'].value_counts().reindex(
        ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    )

    # Create the heatmap
    fig, ax = plt.subplots(figsize=(8, 2))  # Create a matplotlib figure and axes
    sns.heatmap(pd.DataFrame(day_counts).T, annot=True, fmt="d", cmap="Blues", ax=ax, cbar=False)
    ax.set_ylabel("")
    ax.set_xlabel("Day of the Week")
    
    plt.tight_layout()
    return fig  # Return the figure, not a string or file path

def process_instagram_file(files):
    """Processes Instagram JSON data, extracts insights, and generates visualizations."""
    try:
        all_data = []

        # Process the uploaded files
        for file in files:
            try:
                data = json.load(file)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON file {getattr(file, 'filename', 'unknown')}: {e}")
                continue

            # Extract relevant data
            for key, category in [
                ('saved_saved_media', 'Saved Media'),
                ('likes_media_likes', 'Liked Media'),
                ('impressions_history_posts_seen', 'Posts Seen'),
                ('impressions_history_chaining_seen', 'Chaining Seen'),
                ('impressions_history_videos_watched', 'Videos Watched')
            ]:
                if key in data:
                    for item in data[key]:
                        try:
                            logger.debug(f"Processing item: {json.dumps(item, indent=2)}")

                            timestamp = None
                            href = "N/A"

                            if key in ['saved_saved_media', 'likes_media_likes']:
                                if 'string_list_data' in item and item['string_list_data']:
                                    timestamp = item['string_list_data'][0].get('timestamp', None)
                                    href = item['string_list_data'][0].get('href', '')

                            elif key in ['impressions_history_posts_seen', 'impressions_history_videos_watched']:
                                if 'string_map_data' in item and 'Time' in item['string_map_data']:
                                    timestamp = item['string_map_data']['Time'].get('timestamp', None)

                            elif key == 'impressions_history_chaining_seen':
                                timestamp = item['string_list_data'][0].get('timestamp', None)

                            if timestamp is None:
                                logger.warning(f"No timestamp found for item: {json.dumps(item, indent=2)}")

                            # Convert timestamp from Unix to datetime
                            if timestamp:
                                timestamp = pd.to_datetime(timestamp, unit='s', errors='coerce')

                            all_data.append({
                                'title': item.get('title', 'No Title'),
                                'href': href,
                                'timestamp': timestamp,
                                'category': category
                            })

                        except KeyError as e:
                            logger.warning(f"Missing key {e} in section {category} for file {getattr(file, 'filename', 'unknown')}")

        if not all_data:
            logger.warning("No valid data found in uploaded Instagram files.")
            return pd.DataFrame(), None, {}, None, None, False

        # Convert to DataFrame
        df = pd.DataFrame(all_data)

        # Ensure proper datetime formatting for 'timestamp'
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce').dt.date
        df = df.dropna(subset=['timestamp'])

        if df.empty:
            logger.warning("No valid timestamps found in Instagram data.")
            return pd.DataFrame(), None, {}, None, None, False

        # Extract insights
        time_frame_start = df['timestamp'].min()
        time_frame_end = df['timestamp'].max()
        insights = {
            'total_entries': len(df),
            'time_frame_start': time_frame_start,
            'time_frame_end': time_frame_end
        }

        # Prepare data for visualization
        df['year'] = pd.to_datetime(df['timestamp']).dt.year
        df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.day_name()

        # Count activity per day of the week
        day_counts = df['day_of_week'].value_counts().reindex(
            ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        )

        # Exclude 'Unknown' categories and get top 5 per year
        category_data = df.groupby(['year', 'category']).size().reset_index(name='engagement_count')
        top_categories_per_year = category_data.groupby('year').apply(lambda x: x.nlargest(5, 'engagement_count')).reset_index(drop=True)
        top_categories_per_year['rank'] = top_categories_per_year.groupby('year')['engagement_count'].rank(ascending=False, method='first')

        # Generate bump chart and heatmap
        bump_chart_fig = generate_custom_bump_chart(top_categories_per_year)  # Get the figure
        bump_chart_name = save_image_temp_file(bump_chart_fig)  # Save the figure as a file
        
        heatmap_fig = generate_heatmap(df)  # Generate the heatmap figure
        heatmap_name = save_image_temp_file(heatmap_fig)  # Save the heatmap as a file
        
        # Generate a preview of the CSV (first 5 rows) and convert to CSV string
        csv_preview_html = df.head(5).to_html(classes="table table-striped", index=False)

        has_valid_data = not df.empty  # This will be True if df is not empty

        # Save CSV to a user-specific temporary file
        temp_dir = get_user_temp_dir()  # Get session-specific temp directory
        unique_filename = f"{uuid.uuid4()}.csv"
        temp_file_path = os.path.join(temp_dir, unique_filename)

        df.to_csv(temp_file_path, index=False)

        # Return
        return df, unique_filename, insights, bump_chart_name, heatmap_name, csv_preview_html, has_valid_data


    except Exception as e:
        logger.exception(f"Error processing Instagram data: {e}")
        raise ValueError("An internal error occurred. Please try again.")

