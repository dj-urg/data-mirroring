import json
import pandas as pd
import re
import os
import tempfile
import uuid
import logging
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
import seaborn as sns
from matplotlib.lines import Line2D
from app.utils.file_manager import get_user_temp_dir
import squarify
from app.utils.file_validation import parse_json_file, safe_save_file
from werkzeug.datastructures import FileStorage
import openpyxl
import numpy as np

# Use 'Agg' backend to avoid GUI issues
matplotlib.use('Agg')

# Configure the logger
FLASK_ENV = os.getenv('FLASK_ENV', 'production')
logging_level = logging.DEBUG if FLASK_ENV == 'development' else logging.WARNING
logging.basicConfig(level=logging_level, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger()

def save_image_temp_file(fig):
    """Saves an image in the user's temporary directory and returns the filename."""
    temp_dir = get_user_temp_dir()  # Get session-specific temp directory
    unique_filename = f"{uuid.uuid4()}.png"  # Generate a unique filename
    temp_file_path = os.path.join(temp_dir, unique_filename)

    fig.savefig(temp_file_path, bbox_inches='tight')  # Save the image in the session temp directory
    plt.close(fig)  # Free up memory
    logger.debug(f"Image saved at {temp_file_path}")  # Log the saved path for debugging
    return unique_filename  # Return just the filename

# --- Chart Function ---
def generate_custom_bump_chart(
    channel_ranking,
    title="",
    label_length_limit=25,
    figure_width=18,
    figure_height_scale=0.6
    ):
    """
    Generate an alluvial diagram with labels showing rank on first appearance
    and all text set to black.

    Args:
        channel_ranking: DataFrame with columns 'author'/'channel', 'year', 'rank',
                         and optionally 'engagement_count'.
        title (str): The title for the chart.
        label_length_limit (int): Max characters for author/channel names in labels.
        figure_width (float): Width of the matplotlib figure in inches.
        figure_height_scale (float): Factor to scale figure height by number of channels.

    Returns:
        matplotlib.figure.Figure: The figure object containing the chart.
    """
    # --- Input Validation ---
    if not {'year', 'rank'}.issubset(channel_ranking.columns):
        raise ValueError("DataFrame must contain 'year' and 'rank' columns.")
    if 'channel' not in channel_ranking.columns and 'author' not in channel_ranking.columns:
         raise ValueError("DataFrame must contain either 'channel' or 'author' column.")
    channel_col = 'channel' if 'channel' in channel_ranking.columns else 'author'
    has_engagement = 'engagement_count' in channel_ranking.columns

    # --- Data Preparation ---
    df = channel_ranking.copy()
    if has_engagement:
        df['engagement_count'] = pd.to_numeric(df['engagement_count'], errors='coerce')
        df['engagement_count'] = df['engagement_count'].fillna(-np.inf)
    df['year'] = df['year'].astype(int)
    df['rank'] = df['rank'].astype(int) # Ensure rank is integer if used for sorting
    years = sorted(df['year'].unique())
    channels = df[channel_col].unique()

    # --- Figure Setup ---
    figure_height = max(8, len(channels) * figure_height_scale)
    fig, ax = plt.subplots(figsize=(figure_width, figure_height), dpi=120)

    # --- Colors, Constants ---
    cmap = plt.get_cmap("tab20" if len(channels) > 10 else "tab10")
    channel_colors = {channel: cmap(i % cmap.N) for i, channel in enumerate(channels)}

    node_width = 0.6
    node_spacing = 0.2
    year_spacing = (figure_width - 3) / max(1, len(years) - 1) if len(years) > 1 else 3
    node_height = 0.7
    label_offset = 0.15
    left_margin = 2.5 # Slightly more margin maybe needed for rank in label

    # --- Tracking ---
    nodes_by_year_channel = {}

    # --- Draw Flow Function (Unchanged from V3) ---
    def draw_flow(start_x, start_y, end_x, end_y, height1, height2, color, alpha=0.6):
        height_factor = 4.0
        cp1_x = start_x + (end_x - start_x) * 0.35; cp2_x = start_x + (end_x - start_x) * 0.65
        top_curve = [(start_x, start_y + (height1 / height_factor)), (cp1_x, start_y + (height1 / height_factor)), (cp2_x, end_y + (height2 / height_factor)), (end_x, end_y + (height2 / height_factor))]
        bottom_curve = [(end_x, end_y - (height2 / height_factor)), (cp2_x, end_y - (height2 / height_factor)), (cp1_x, start_y - (height1 / height_factor)), (start_x, start_y - (height1 / height_factor))]
        verts = top_curve + bottom_curve + [(start_x, start_y + (height1 / height_factor))]
        codes = [Path.MOVETO] + [Path.CURVE4] * 3 + [Path.LINETO] + [Path.CURVE4] * 3 + [Path.CLOSEPOLY]
        path = Path(verts, codes); patch = patches.PathPatch(path, facecolor=color, alpha=alpha, edgecolor='none', lw=0)
        ax.add_patch(patch)

    # --- Draw Nodes and First-Appearance Labels with Rank ---
    max_nodes_in_year = 0
    for year_idx, year in enumerate(years):
        x_pos = left_margin + year_idx * year_spacing
        year_data = df[df['year'] == year].copy()

        # Define sort key based on available columns
        # Note: using rank from input data only if engagement is not present
        sort_col = 'engagement_count' if has_engagement else 'rank'
        ascending_sort = False if has_engagement else True # Desc for engagement, Asc for rank

        year_data = year_data.sort_values(sort_col, ascending=ascending_sort)
        year_data.reset_index(drop=True, inplace=True) # Reset index to get 0-based position

        max_nodes_in_year = max(max_nodes_in_year, len(year_data))

        for i, row in year_data.iterrows(): # Use simple iterrows after reset_index
            channel = row[channel_col]
            if pd.isna(channel): continue

            max_items = len(year_data) # Use length after potential filtering/sorting
            y_pos = (max_items - 1 - i) * (node_height + node_spacing) # Position based on 0-index 'i'
            node_color = channel_colors.get(channel, 'grey')

            # Draw Node
            rect = patches.Rectangle(
                (x_pos, y_pos), node_width, node_height,
                facecolor=node_color, edgecolor='white', linewidth=0.5, alpha=0.9
            )
            ax.add_patch(rect)

            # --- Label Above Every Node ---
            name_part = str(channel)
            # Truncate if needed (consider shorter limit if placing above node)
            if len(name_part) > (label_length_limit - 5): # Slightly shorter limit maybe
                name_part = name_part[:label_length_limit-8] + "..."
            label_text = name_part

            # Define a small vertical offset for the label above the node
            label_vertical_offset = 0.05

            ax.text(
                x_pos + node_width / 2,                 # Center horizontally on the node
                y_pos + node_height + label_vertical_offset, # Position slightly above the node top
                label_text,
                va='bottom',       # Vertical alignment: text bottom sits above the y-coord
                ha='center',       # Horizontal alignment: center
                fontsize=7,        # Smaller font size likely needed
                fontweight='normal',
                color='black'
            )

            # --- Engagement Count Label (Inside Node, Black Text) ---
            if has_engagement and row['engagement_count'] != -np.inf:
                engagement_count = int(row['engagement_count'])
                ax.text(
                    x_pos + node_width / 2, y_pos + node_height / 2, f"{engagement_count:,}",
                    va='center', ha='center', fontsize=8,
                    fontweight='bold', color='black' # Explicitly black
                )

            # Store node position
            nodes_by_year_channel[(year, channel)] = (x_pos, y_pos, node_height)

    # --- Draw Connections (Unchanged from V3) ---
    for channel in channels:
        if pd.isna(channel): continue
        channel_data = df[df[channel_col] == channel]
        channel_years = sorted(channel_data['year'].unique())
        for i in range(len(channel_years) - 1):
            year1, year2 = channel_years[i], channel_years[i+1]
            if (year1, channel) in nodes_by_year_channel and (year2, channel) in nodes_by_year_channel:
                node1_x, node1_y, node1_h = nodes_by_year_channel[(year1, channel)]
                node2_x, node2_y, node2_h = nodes_by_year_channel[(year2, channel)]
                draw_flow(node1_x + node_width, node1_y + node1_h / 2, node2_x, node2_y + node2_h / 2, node1_h, node2_h, channel_colors.get(channel, 'grey'), alpha=0.5)

    # --- Year Labels (Bottom, Black Text) ---
    year_label_y = -0.5
    for year_idx, year in enumerate(years):
        ax.text(
            left_margin + year_idx * year_spacing + node_width / 2, year_label_y, str(year),
            ha='center', va='top', fontsize=11,
            fontweight='bold', color='black' # Explicitly black
        )

    # --- Set Limits and Appearance ---
    right_limit = left_margin + (len(years) - 1) * year_spacing + node_width + 1.0
    ax.set_xlim(0, right_limit)
    ax.set_ylim(year_label_y - 0.5 , max_nodes_in_year * (node_height + node_spacing) + 0.5)

    ax.set_title(title, fontsize=16, fontweight='bold', pad=25, color='black') # Explicitly black
    ax.set_axis_off()

    fig.tight_layout(rect=[0.02, 0.05, 0.98, 0.95])

    return fig

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

# New heatmap functions to add to your Instagram processor

def generate_month_heatmap(df):
    """Generates a heatmap showing Instagram engagement by month with absolutely no grid lines."""
    # Extract month and year from timestamp
    df['month'] = pd.to_datetime(df['timestamp']).dt.month
    df['year'] = pd.to_datetime(df['timestamp']).dt.year
    
    # Create a pivot table to count posts by month and year
    month_counts = df.pivot_table(
        index='year', 
        columns='month', 
        values='title', 
        aggfunc='count', 
        fill_value=0
    )
    
    # Map month numbers to month names
    month_names = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
        7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }
    month_counts.columns = [month_names[m] for m in month_counts.columns]
    
    # Create figure with larger size to accommodate larger values
    fig, ax = plt.subplots(figsize=(10, len(month_counts) * 0.6))
    
    # Create heatmap with all possible grid lines removed
    sns.heatmap(
        month_counts, 
        annot=True,          # Show numbers in cells
        fmt="d",             # Format as integers
        cmap="Blues",        # Blue color map
        ax=ax,               # Use the created axis
        cbar=False,          # No color bar
        linewidths=0,        # No grid lines between cells
        linecolor='none',    # No line color
        annot_kws={"size": 10}  # Increase annotation text size
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
    ax.set_ylabel("")
    ax.set_xlabel("")
    
    # Increase font size of tick labels
    ax.tick_params(labelsize=11)
    
    # Increase the cell size
    plt.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.15)
    
    # Turn off all grid lines
    ax.grid(False)
    
    # Use a more flexible layout approach instead of tight_layout
    plt.tight_layout(pad=0.5)
    return fig

def generate_time_of_day_heatmap(df):
    """Generates a heatmap showing Instagram engagement by time of day with no grid lines."""
    # Extract hour from timestamp (requires using timestamp as datetime, not date)
    # Using original timestamp before conversion to date in the main processing function
    if 'timestamp' in df.columns and pd.api.types.is_datetime64_dtype(df['timestamp']):
        df_with_hour = df.copy()
    else:
        # Try to convert or use a different approach if timestamp is not datetime
        logger.warning("Timestamp column is not in datetime format for time of day analysis.")
        return None
        
    # Extract hour from timestamp
    df_with_hour['hour'] = df_with_hour['timestamp'].dt.hour
    
    # Count posts by hour
    hour_counts = df_with_hour['hour'].value_counts().sort_index()
    
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
    df_with_hour['time_range'] = df_with_hour['hour'].map(time_ranges)
    time_range_counts = df_with_hour['time_range'].value_counts().reindex([
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
    ax.set_xlabel("")
    
    # Turn off all grid lines
    ax.grid(False)
    
    plt.tight_layout()
    return fig

# Update the day of week heatmap for consistency
def generate_heatmap(df):
    """Generates a heatmap showing Instagram engagement by day of the week with no grid lines."""
    if 'timestamp' not in df.columns:
        logger.warning("Timestamp column not found in the DataFrame.")
        return None  # Or raise an exception, based on your preference

    # Prepare the data
    df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.day_name()
    day_counts = df['day_of_week'].value_counts().reindex(
        ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    )

    # Create the heatmap
    day_count_df = pd.DataFrame({'Day': day_counts.index, 'Count': day_counts.values}).set_index('Day')
    
    # Create figure and axes
    fig, ax = plt.subplots(figsize=(8, 2))
    
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
    
    # Turn off axis ticks - removes the small lines at the edges
    ax.tick_params(axis='both', which='both', length=0)
    
    # Clear the top and right spines specifically
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Keep axis labels
    ax.set_ylabel("")
    ax.set_xlabel("")
    
    # Turn off all grid lines
    ax.grid(False)
    
    plt.tight_layout()
    return fig

def generate_author_treemap(df):
    """Generates a treemap of top authors based on engagement count."""
    
    # Filter for non-unknown authors
    authors_df = df[df['author'] != 'Unknown']
    
    if authors_df.empty:
        # Fallback to categories if no author data
        author_data = df.groupby('category').size().reset_index(name='count')
        author_data.columns = ['author', 'count']  # Rename for consistency
    else:
        # Group by author and count engagements
        author_data = authors_df.groupby('author').size().reset_index(name='count')
    
    # Sort by engagement count and get top 15 authors
    author_data = author_data.sort_values('count', ascending=False).head(15)
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Calculate normalized sizes based on counts
    sizes = author_data['count'].values
    labels = [f"{author}\n({count})" if len(author) < 15 else f"{author[:12]}...\n({count})" 
              for author, count in zip(author_data['author'], author_data['count'])]
    
    # Create color map
    cmap = plt.get_cmap('Blues')
    norm = plt.Normalize(min(sizes), max(sizes))
    colors = [cmap(norm(size)) for size in sizes]
    
    # Create the treemap
    squarify.plot(sizes=sizes, label=labels, color=colors, alpha=0.8, ax=ax)
    
    # Remove axes and spines
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    # Add title
    ax.set_title("", fontsize=14)
    
    plt.tight_layout()
    return fig

def process_instagram_file(files):
    """Processes Instagram JSON data, extracts insights, and generates visualizations."""
    try:
        # Debug information for file uploads
        file_count = len(files) if files else 0
        logger.info(f"Processing {file_count} Instagram file(s)")
        
        # Collect filenames for logging
        filenames = []
        for file in files:
            filename = getattr(file, 'filename', 'unknown')
            filenames.append(filename)
            logger.info(f"Processing file: {filename}")
            
        all_data = []
        processed_files = []  # New list to track what files were processed

        # Process the uploaded files
        for file in files:
            try:
                file_name = getattr(file, 'filename', 'unknown')
                logger.info(f"Processing Instagram file: {file_name}")
                processed_files.append(file_name)  # Add to processed files list
                
                data, error = parse_json_file(file)
                if error:
                    logger.warning(f"Failed to parse JSON file {file_name}: {error}")
                    continue
            except Exception as e:
                logger.warning(f"Failed to parse JSON file {file_name}: {e}")
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
                            author = "Unknown"  # Default author value

                            if key == 'saved_saved_media':
                                # Handle saved_saved_media with string_map_data
                                if 'string_map_data' in item and 'Saved on' in item['string_map_data']:
                                    saved_on = item['string_map_data']['Saved on']
                                    timestamp = saved_on.get('timestamp', None)
                                    href = saved_on.get('href', '')
                                    author = item.get('title', 'Unknown')

                            elif key in ['saved_saved_media', 'likes_media_likes']:
                                if 'string_list_data' in item and item['string_list_data']:
                                    timestamp = item['string_list_data'][0].get('timestamp', None)
                                    href = item['string_list_data'][0].get('href', '')
                                    # Try to extract author/title
                                    title = item.get('title', 'No Title')
                                    if title != 'No Title':
                                        author = title

                            elif key in ['impressions_history_posts_seen', 'impressions_history_videos_watched']:
                                if 'string_map_data' in item and 'Time' in item['string_map_data']:
                                    timestamp = item['string_map_data']['Time'].get('timestamp', None)
                                    
                                    # Extract author from videos_watched format
                                    if 'Author' in item['string_map_data']:
                                        author = item['string_map_data']['Author'].get('value', 'Unknown')

                            elif key == 'impressions_history_chaining_seen':
                                if 'string_list_data' in item and item['string_list_data']:
                                    timestamp = item['string_list_data'][0].get('timestamp', None)

                            if timestamp is None:
                                logger.warning(f"No timestamp found for item: {json.dumps(item, indent=2)}")
                                continue  # Skip items without timestamp

                            # Convert timestamp from Unix to datetime
                            if timestamp:
                                try:
                                    timestamp = pd.to_datetime(timestamp, unit='s', errors='coerce')
                                except ValueError:
                                    logger.warning(f"Invalid timestamp format: {timestamp}")
                                    timestamp = None

                            # Skip entries with invalid timestamps
                            if timestamp is None:
                                continue

                            # Add the extracted data
                            all_data.append({
                                'title': item.get('title', 'No Title'),
                                'href': href,
                                'timestamp': timestamp,
                                'category': category,
                                'author': author  # Add author field
                            })

                        except KeyError as e:
                            logger.warning(f"Missing key {e} in section {category} for file {getattr(file, 'filename', 'unknown')}")

        if not all_data:
            logger.warning("No valid data found in uploaded Instagram files.")
            return pd.DataFrame(), None, {}, None, None, None, None, False, False

        # Convert to DataFrame
        df = pd.DataFrame(all_data)
        
        # Log data statistics for debugging
        logger.info(f"Processed {len(df)} Instagram records from {len(set(df['category']))} categories")
        category_counts = df['category'].value_counts()
        for cat, count in category_counts.items():
            logger.info(f"  - {cat}: {count} records")

        # Store original timestamp for time of day analysis
        df_with_time = df.copy()
        
        # Ensure proper datetime formatting for 'timestamp'
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce').dt.date
        df = df.dropna(subset=['timestamp'])

        if df.empty:
            logger.warning("No valid timestamps found in Instagram data.")
            return pd.DataFrame(), None, {}, None, None, None, None, False, False

        # Extract insights
        time_frame_start = df['timestamp'].min()
        time_frame_end = df['timestamp'].max()
        insights = {
            'total_entries': len(df),
            'time_frame_start': time_frame_start,
            'time_frame_end': time_frame_end,
            'videos_watched': len(df[df['category'] == 'Videos Watched']),
            'unique_authors': df['author'].nunique()
        }

        # Prepare data for visualization
        df['year'] = pd.to_datetime(df['timestamp']).dt.year
        df['month_name'] = pd.to_datetime(df['timestamp']).dt.strftime('%B')
        df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.day_name()

        # Count activity per day of the week
        day_counts = df['day_of_week'].value_counts().reindex(
            ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        )

        # Use author instead of category for the bump chart
        # Focus on entries with known authors (not 'Unknown')
        authors_df = df[df['author'] != 'Unknown']
        
        if authors_df.empty:
            logger.warning("No valid author data found. Using categories instead.")
            # Fallback to categories if no author data
            author_data = df.groupby(['year', 'category']).size().reset_index(name='engagement_count')
            top_authors_per_year = author_data.groupby('year').apply(lambda x: x.nlargest(5, 'engagement_count')).reset_index(drop=True)
            top_authors_per_year['rank'] = top_authors_per_year.groupby('year')['engagement_count'].rank(ascending=False, method='first')
            top_authors_per_year = top_authors_per_year.rename(columns={'category': 'author'})
        else:
            # Get top 5 authors per year based on engagement count
            author_data = authors_df.groupby(['year', 'author']).size().reset_index(name='engagement_count')
            top_authors_per_year = author_data.groupby('year').apply(lambda x: x.nlargest(5, 'engagement_count')).reset_index(drop=True)
            top_authors_per_year['rank'] = top_authors_per_year.groupby('year')['engagement_count'].rank(ascending=False, method='first')


        # Generate category/author bump chart
        if len(top_authors_per_year) > 0 and len(top_authors_per_year['year'].unique()) > 1:
            bump_chart_fig = generate_custom_bump_chart(top_authors_per_year)
            bump_chart_name = save_image_temp_file(bump_chart_fig)
        else:
            # Fallback to treemap if not enough years for a bump chart
            author_treemap_fig = generate_author_treemap(df)
            bump_chart_name = save_image_temp_file(author_treemap_fig)

        # Generate day of week heatmap
        day_heatmap_fig = generate_heatmap(df)
        day_heatmap_name = save_image_temp_file(day_heatmap_fig)
        
        # Generate month heatmap
        month_heatmap_fig = generate_month_heatmap(df)
        month_heatmap_name = save_image_temp_file(month_heatmap_fig)
        
        # Generate time of day heatmap (using the original timestamps with time info)
        time_heatmap_fig = generate_time_of_day_heatmap(df_with_time)
        time_heatmap_name = save_image_temp_file(time_heatmap_fig) if time_heatmap_fig is not None else None
        
        # Generate HTML preview from DataFrame
        raw_html = df.head(5).to_html(
            classes="table table-striped text-right",
            index=False,
            escape=False,
            render_links=True,
            border=0
        )
        
        # Generate a preview of the CSV
        csv_preview_html = re.sub(r'style="[^"]*"', '', raw_html)

        has_valid_data = not df.empty
        
        # Create CSV content
        csv_content = df.to_csv(index=False)
        
        # Use a temporary file and then save it safely
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
            temp_file.write(csv_content.encode('utf-8'))
            temp_file_path = temp_file.name
        
        # Get a unique filename
        unique_filename = f"{uuid.uuid4()}.csv"
        
        # Save to user temp dir using the safe function
        temp_dir = get_user_temp_dir()
        
        # Convert the file to a FileStorage object for safe_save_file
        with open(temp_file_path, 'rb') as f:
            file_storage = FileStorage(
                stream=f,
                filename=unique_filename,
                content_type='text/csv'
            )
            safe_file_path = safe_save_file(file_storage, unique_filename, temp_dir)
        
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        # Return all data including the new heatmaps
        return df, unique_filename, insights, bump_chart_name, day_heatmap_name, month_heatmap_name, time_heatmap_name, csv_preview_html, has_valid_data

    except Exception as e:
        logger.exception(f"Error processing Instagram data: {e}")
        raise ValueError("An internal error occurred. Please try again.")