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
from app.utils.file_manager import get_user_temp_dir
import csv
from app.utils.file_validation import parse_json_file, safe_save_file
from werkzeug.datastructures import FileStorage
import openpyxl

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
    
    # Replace all newline characters in the DataFrame (avoid breaking CSV format when opening in Excel)
    df.replace(r'\n', ' ', regex=True, inplace=True)
    df.to_csv(temp_file_path, index=False, quoting=csv.QUOTE_ALL, encoding='utf-8')  # Save the CSV in the session temp directory
    os.chmod(temp_file_path, 0o600)  # Secure file permissions
    logger.debug(f"CSV saved at {temp_file_path}")  # Log the saved path for debugging
    return unique_filename  # Return just the filename

def save_excel_temp_file(df):
    """Saves Excel data in the user's temporary directory and returns the filename."""
    temp_dir = get_user_temp_dir()  # Get session-specific temp directory
    unique_filename = f"{uuid.uuid4()}.xlsx"  # Generate a unique filename
    temp_file_path = os.path.join(temp_dir, unique_filename)

    # Create a copy of the DataFrame to avoid modifying the original
    excel_df = df.copy()
    
    # Convert timezone-aware datetime columns to timezone-naive
    for col in excel_df.select_dtypes(include=['datetime64[ns, UTC]']).columns:
        excel_df[col] = excel_df[col].dt.tz_localize(None)
    
    # Replace newline characters to ensure proper formatting in Excel
    excel_df.replace(r'\n', ' ', regex=True, inplace=True)

    # Save the DataFrame as an Excel file
    excel_df.to_excel(temp_file_path, index=False, engine='openpyxl')
    os.chmod(temp_file_path, 0o600)  # Secure file permissions
    logger.debug(f"Excel file saved at {temp_file_path}")  # Log the saved path for debugging
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
    """Generates a heatmap showing YouTube engagement by day of the week with no grid lines."""
    # Convert day counts to a dataframe
    day_count_df = pd.DataFrame({'Day': day_counts.index, 'Count': day_counts.values}).set_index('Day')
    
    # Create a heatmap
    fig, ax = plt.subplots(figsize=(8, 2))  # Adjust size for heatmap
    
    # Create heatmap with all grid lines removed
    sns.heatmap(
        day_count_df.T, 
        annot=True, 
        fmt="d", 
        cmap="Blues", 
        ax=ax, 
        cbar=False,
        linewidths=0,        # No grid lines between cells
        linecolor='none'     # No line color
    )
    
    # Remove all spines
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    # Turn off axis ticks - this removes the small lines at the edges
    ax.tick_params(axis='both', which='both', length=0)
    
    # Clear the top and right spines specifically (these often remain)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Keep axis labels empty
    ax.set_ylabel("")
    ax.set_xlabel("")
    
    # Turn off all grid lines
    ax.grid(False)
    
    plt.tight_layout()
    
    # Return the figure
    return fig

# New functions to add to src/app/handlers/youtube.py

def generate_month_heatmap(df):
    """Generates a heatmap showing YouTube engagement by month with absolutely no grid lines."""
    # Extract month and year from timestamp
    df['month'] = pd.to_datetime(df['timestamp']).dt.month
    df['year'] = pd.to_datetime(df['timestamp']).dt.year
    
    # Create a pivot table to count videos by month and year
    month_counts = df.pivot_table(
        index='year', 
        columns='month', 
        values='video_title', 
        aggfunc='count', 
        fill_value=0
    )
    
    # Map month numbers to month names
    month_names = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
        7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }
    month_counts.columns = [month_names[m] for m in month_counts.columns]
    
    # Create figure and axes
    fig, ax = plt.subplots(figsize=(8, 2))
    
    # Create heatmap with all possible grid lines removed
    sns.heatmap(
        month_counts, 
        annot=True,          # Show numbers in cells
        fmt="d",             # Format as integers
        cmap="Blues",        # Blue color map
        ax=ax,               # Use the created axis
        cbar=False,          # No color bar
        linewidths=0,        # No grid lines between cells
        linecolor='none'     # No line color
    )
    
    # Remove all spines
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    # Turn off axis ticks - this removes the small lines at the edges
    ax.tick_params(axis='both', which='both', length=0)
    
    # Clear the top and right spines specifically (these often remain)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Customize axis labels
    ax.set_ylabel("Year", fontsize=10)
    ax.set_xlabel("Month", fontsize=10)
    
    # Remove the title
    ax.set_title("")
    
    # Turn off all grid lines
    ax.grid(False)
    
    plt.tight_layout()
    return fig

def generate_time_of_day_heatmap(df):
    """Generates a heatmap showing YouTube engagement by time of day with no grid lines."""
    # Extract hour from timestamp
    df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
    
    # Count videos by hour
    hour_counts = df['hour'].value_counts().sort_index()
    
    # Create time ranges for better visualization (4-hour blocks)
    time_ranges = {
        0: '12-4 AM', 1: '12-4 AM', 2: '12-4 AM', 3: '12-4 AM',
        4: '4-8 AM', 5: '4-8 AM', 6: '4-8 AM', 7: '4-8 AM',
        8: '8-12 PM', 9: '8-12 PM', 10: '8-12 PM', 11: '8-12 PM',
        12: '12-4 PM', 13: '12-4 PM', 14: '12-4 PM', 15: '12-4 PM',
        16: '4-8 PM', 17: '4-8 PM', 18: '4-8 PM', 19: '4-8 PM',
        20: '8-12 AM', 21: '8-12 AM', 22: '8-12 AM', 23: '8-12 AM'
    }
    
    # Group by time ranges
    df['time_range'] = df['hour'].map(time_ranges)
    time_range_counts = df['time_range'].value_counts().reindex([
        '12-4 AM', '4-8 AM', '8-12 PM', '12-4 PM', '4-8 PM', '8-12 AM'
    ])
    
    # Create the heatmap
    hour_count_df = pd.DataFrame({'Time': time_range_counts.index, 'Count': time_range_counts.values}).set_index('Time')
    
    # Create figure and axes
    fig, ax = plt.subplots(figsize=(8, 2))
    
    # Create heatmap with all grid lines removed
    sns.heatmap(
        hour_count_df.T, 
        annot=True, 
        fmt="d", 
        cmap="Blues", 
        ax=ax, 
        cbar=False,
        linewidths=0,        # No grid lines between cells
        linecolor='none'     # No line color
    )
    
    # Remove all spines
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    # Turn off axis ticks - removes the small lines at the edges
    ax.tick_params(axis='both', which='both', length=0)
    
    # Clear the top and right spines specifically
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Keep axis labels
    ax.set_ylabel("")
    ax.set_xlabel("Time of Day", fontsize=10)
    
    # Turn off all grid lines
    ax.grid(False)
    
    plt.tight_layout()
    return fig

# Main data processing function
def process_youtube_file(files):
    """Processes multiple YouTube JSON data files and returns insights and plot data."""
    try:
        all_data = []

        for file in files:
            try:
                # Use secure JSON parsing from validation module
                data, error = parse_json_file(file)
                if error:
                    logger.warning(f"Failed to parse YouTube JSON file: {error}")
                    continue
                
                flattened_data = []

                # Process each item with validation
                for item in data:
                    # Validate item is a dict
                    if not isinstance(item, dict):
                        logger.warning(f"Skipping non-dict item in YouTube data: {type(item)}")
                        continue
                        
                    # Extract and validate subtitle info
                    subtitles = item.get('subtitles', [{}])
                    if not isinstance(subtitles, list):
                        subtitles = [{}]  # Fallback for invalid data
                        
                    subtitle_name = subtitles[0].get('name', 'Unknown') if subtitles else 'Unknown'
                    subtitle_url = subtitles[0].get('url', '') if subtitles else ''
                    
                    # Validate and sanitize URL
                    if subtitle_url and not subtitle_url.startswith(('http://', 'https://')):
                        subtitle_url = ''  # Clear invalid URLs
                    
                    # Extract and validate timestamp
                    time_str = item.get('time', '')
                    timestamp = pd.to_datetime(time_str, errors='coerce')
                    
                    # Skip items with invalid timestamps
                    if pd.isnull(timestamp):
                        logger.warning(f"Skipping YouTube item with invalid timestamp: {time_str}")
                        continue
                    
                    # Extract and sanitize title and URL
                    video_title = item.get('title', 'No Title')
                    if not isinstance(video_title, str):
                        video_title = 'No Title'
                        
                    video_url = item.get('titleUrl', '')
                    if video_url and not video_url.startswith(('http://', 'https://')):
                        video_url = ''  # Clear invalid URLs
                    
                    flattened_data.append({
                        'video_title': video_title,
                        'video_url': video_url,
                        'timestamp': timestamp,
                        'channel': subtitle_name,
                        'channel_url': subtitle_url
                    })
                    
                all_data.extend(flattened_data)
                
            except Exception as e:
                logger.warning(f"Error processing YouTube file: {str(e)}")
                continue

        # Check if we have valid data
        if not all_data:
            logger.warning("No valid data found in uploaded YouTube files")
            raise ValueError("No valid data found in the uploaded files. Please check the file format.")

        df = pd.DataFrame(all_data)
        
        # Generate insights
        insights = {
            'total_videos': len(df),
            'time_frame_start': df['timestamp'].min().date() if not df.empty else 'N/A',
            'time_frame_end': df['timestamp'].max().date() if not df.empty else 'N/A',
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

        # Generate day of week heatmap image
        day_heatmap_name = save_image_temp_file(generate_heatmap(day_counts))
        
        # Generate month heatmap image
        month_heatmap_name = save_image_temp_file(generate_month_heatmap(df))
        
        # Generate time of day heatmap image
        time_heatmap_name = save_image_temp_file(generate_time_of_day_heatmap(df))

        # Save CSV data securely
        csv_content = df.to_csv(index=False, quoting=csv.QUOTE_ALL, encoding='utf-8')
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
            temp_file.write(csv_content.encode('utf-8'))
            temp_file_path = temp_file.name
            
        csv_filename = f"{uuid.uuid4()}.csv"
        with open(temp_file_path, 'rb') as f:
            file_storage = FileStorage(
                stream=f,
                filename=csv_filename,
                content_type='text/csv'
            )
            safe_file_path = safe_save_file(file_storage, csv_filename)
            unique_filename = os.path.basename(safe_file_path)
        
        # Clean up temp file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            
        # Save Excel data securely
        excel_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        excel_file.close()
        
        # Convert timezone-aware datetime columns to timezone-naive for Excel
        excel_df = df.copy()
        for col in excel_df.select_dtypes(include=['datetime64[ns, UTC]']).columns:
            excel_df[col] = excel_df[col].dt.tz_localize(None)
        
        # Replace newlines to avoid breaking Excel format
        excel_df.replace(r'\n', ' ', regex=True, inplace=True)
        
        # Save using openpyxl
        excel_df.to_excel(excel_file.name, index=False, engine='openpyxl')
        
        excel_filename_uuid = f"{uuid.uuid4()}.xlsx"
        with open(excel_file.name, 'rb') as f:
            file_storage = FileStorage(
                stream=f,
                filename=excel_filename_uuid,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            excel_file_path = safe_save_file(file_storage, excel_filename_uuid)
            excel_filename = os.path.basename(excel_file_path)
            
        # Clean up temp file
        if os.path.exists(excel_file.name):
            os.remove(excel_file.name)
        
        # Generate HTML preview from DataFrame
        raw_html = df.head(5).to_html(
            classes="table table-striped text-right",
            index=False,
            escape=False,
            render_links=True,
            border=0
        )

        # Remove all inline styles
        csv_preview_html = re.sub(r'style="[^"]*"', '', raw_html)

        return df, excel_filename, unique_filename, insights, bump_chart_name, day_heatmap_name, month_heatmap_name, time_heatmap_name, not df.empty, csv_preview_html

    except ValueError as e:
        # Forward ValueError with its original message
        logger.warning(f"ValueError in YouTube processing: {str(e)}")
        raise ValueError(str(e))
    except Exception as e:
        logger.warning(f"Error processing YouTube data: {type(e).__name__} - {str(e)}")
        raise ValueError("An internal error occurred. Please try again.")