import json
import pandas as pd
import os
import tempfile
import uuid
import logging
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import seaborn as sns
import re
from app.utils.file_utils import get_user_temp_dir

# Use 'Agg' backend to avoid GUI issues
matplotlib.use('Agg')

# Configure the logger
FLASK_ENV = os.getenv('FLASK_ENV', 'production')  # Default to 'production'

if FLASK_ENV == 'production':
    # Disable logging in production except for warnings and errors
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(levelname)s: %(message)s')
else:
    # Enable detailed logging for development
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

logger = logging.getLogger()

# Custom visualization functions
def add_line(ax, year_values, rank_values, linewidth=3, color="black"):
    ax.add_artist(Line2D(year_values, -rank_values, linewidth=linewidth, color=color))

def add_circle(ax, year_value, rank_value, marker_size=15, color="black"):
    ax.plot(year_value, -rank_value, 'o', color=color, markersize=marker_size)

def add_text(ax, year_value, rank_value, text, offset=0.02):
    ax.text(year_value + offset, -rank_value, text, fontsize=10, va='bottom', ha='left')

def format_ticks(ax, years, padx=0.25, pady=0.1, y_label_size=16, x_label_size=18):
    ax.set(xlim=(-padx, len(years) - 1 + padx), ylim=(-5.5 - pady, -pady))

    xticks = [i for i in range(len(years))]
    ax.set_xticks(ticks=xticks, labels=years)

    # Remove y-axis labels (rank numbers)
    ax.set_yticks([])  # No y-axis tick labels

    # Only show top x-axis labels (years), disable bottom x-axis labels
    ax.tick_params("y", labelsize=y_label_size, pad=8)
    ax.tick_params("x", labeltop=True, bottom=False, labelsize=x_label_size, pad=4)  # Disable bottom ticks

def set_custom_style():
    plt.rcParams.update({
        "axes.facecolor": "#FFFFFF",  # White background for the plot
        "figure.facecolor": "#FFFFFF",  # White background for the figure
        "grid.color": "#E4C9C9",  # Keep grid color subtle
        "axes.grid": True,
        "xtick.bottom": False,
        "xtick.top": True,
        "ytick.left": False,
        "ytick.right": False,
        "axes.spines.left": False,
        "axes.spines.bottom": False,
        "axes.spines.right": False,
        "axes.spines.top": False
    })

# Helper function to save images as temporary files
def save_image_temp_file(fig):
    """Saves an image in the user's temporary directory and returns the filename."""
    temp_dir = get_user_temp_dir()  # Get session-specific temp directory
    unique_filename = f"{uuid.uuid4()}.png"  # Generate a unique filename
    temp_file_path = os.path.join(temp_dir, unique_filename)

    fig.savefig(temp_file_path, bbox_inches='tight')  # Save the image in the session temp directory
    plt.close(fig)  # Free up memory
    logger.debug(f"Image saved at {temp_file_path}")  # Log the saved path for debugging
    return unique_filename  # Return just the filename

# Helper function to save CSV as a temporary file
def save_csv_temp_file(df):
    """Saves CSV data in the user's temporary directory and returns the filename."""
    temp_dir = get_user_temp_dir()  # Get session-specific temp directory
    unique_filename = f"{uuid.uuid4()}.csv"  # Generate a unique filename
    temp_file_path = os.path.join(temp_dir, unique_filename)

    df.to_csv(temp_file_path, index=False)  # Save the CSV in the session temp directory
    os.chmod(temp_file_path, 0o600)  # Secure file permissions
    logger.debug(f"CSV saved at {temp_file_path}")  # Log the saved path for debugging
    return unique_filename  # Return just the filename

def generate_custom_bump_chart(channel_ranking):
    # Set custom style
    set_custom_style()

    # Extract years and ranks for each channel and plot the lines
    channels = channel_ranking['channel'].unique()
    years = sorted(channel_ranking['year'].unique())  # List of years to plot

    # Adjust figure size (reduce height)
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(8, 3))  # Width remains, height reduced significantly

    # Adjust the tick formatting and spacing
    format_ticks(ax, years)

    colors = plt.get_cmap("tab10").colors  # Color palette

    # Draw lines or circles for each channel
    for i, channel in enumerate(channels):
        channel_data = channel_ranking[channel_ranking['channel'] == channel]
        year_values = [years.index(year) for year in channel_data['year']]
        rank_values = channel_data['rank'].values
        color = colors[i % len(colors)]  # Rotate through colors

        if len(year_values) > 1:
            # Draw lines for channels that appear in multiple years
            add_line(ax, year_values, rank_values, color=color)
            for j, year in enumerate(year_values):
                add_circle(ax, year, rank_values[j], color=color)
            add_text(ax, year_values[-1], rank_values[-1], channel)
        else:
            # Draw circles for channels that only appear in one year
            add_circle(ax, year_values[0], rank_values[0], color=color)
            add_text(ax, year_values[0], rank_values[0], channel)

    plt.tight_layout()  # Ensure the plot fits nicely

    # Save the image temporarily and return the filename
    return fig

def generate_heatmap(day_counts):
    # Convert day counts to a dataframe
    day_count_df = pd.DataFrame({'Day': day_counts.index, 'Count': day_counts.values}).set_index('Day')

    # Create a heatmap
    fig, ax = plt.subplots(figsize=(8, 2))  # Adjust size for heatmap
    sns.heatmap(day_count_df.T, annot=True, fmt="d", cmap="Blues", ax=ax, cbar=False)
    ax.set_ylabel("")
    ax.set_xlabel("Day of the Week")

    plt.tight_layout()

    # Save the image temporarily and return the filename
    return fig

# Main data processing function
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
        df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.day_name()  # Get day of the week

        # Count the number of videos consumed on each day of the week
        day_counts = df['day_of_week'].value_counts().reindex(
            ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        )

        # Exclude 'Unknown' channels and get top 5 per year
        channel_data = df.groupby(['year', 'channel']).size().reset_index(name='view_counts')
        channel_data = channel_data[channel_data['channel'] != 'Unknown']
        top_channels_per_year = channel_data.groupby('year').apply(lambda x: x.nlargest(5, 'view_counts')).reset_index(drop=True)

        # Rank channels for each year
        top_channels_per_year['rank'] = top_channels_per_year.groupby('year')['view_counts'].rank(ascending=False, method='first')

        # Generate bump chart image
        bump_chart_name = save_image_temp_file(generate_custom_bump_chart(top_channels_per_year))

        # Generate heatmap image
        heatmap_name = save_image_temp_file(generate_heatmap(day_counts))

        # Save CSV to a user-specific temporary file
        temp_dir = get_user_temp_dir()  # Get session-specific temp directory
        unique_filename = f"{uuid.uuid4()}.csv"
        temp_file_path = os.path.join(temp_dir, unique_filename)

        df.to_csv(temp_file_path, index=False)
        
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

        return df, unique_filename, insights, bump_chart_name, heatmap_name, not df.empty, csv_preview_html


    except Exception as e:
        logger.warning(f"Error occurred: {type(e).__name__} - {str(e)}")  # Avoid logging sensitive data
        raise ValueError("An internal error occurred. Please try again.")