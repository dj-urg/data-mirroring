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
import squarify

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
    """Saves an image in the user's temporary directory and returns the filename."""
    temp_dir = get_user_temp_dir()  # Get session-specific temp directory
    unique_filename = f"{uuid.uuid4()}.png"  # Generate a unique filename
    temp_file_path = os.path.join(temp_dir, unique_filename)

    fig.savefig(temp_file_path, bbox_inches='tight')  # Save the image in the session temp directory
    plt.close(fig)  # Free up memory
    logger.debug(f"Image saved at {temp_file_path}")  # Log the saved path for debugging
    return unique_filename  # Return just the filename

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
    
    # Turn off all grid lines
    ax.grid(False)
    
    plt.tight_layout()
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
    ax.set_xlabel("Time of Day", fontsize=10)
    
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
    ax.set_xlabel("Day of the Week", fontsize=10)
    
    # Turn off all grid lines
    ax.grid(False)
    
    plt.tight_layout()
    return fig

def generate_author_treemap(df):
    """Generates a treemap of top authors based on engagement count."""
    import squarify  # Import squarify locally in the function
    
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
            return pd.DataFrame(), None, {}, None, None, None, None, False

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
            return pd.DataFrame(), None, {}, None, None, None, None, False

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

        # Generate author tree map
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
        
        # Generate a preview of the CSV
        csv_preview_html = df.head(5).to_html(classes="table table-striped", index=False)

        has_valid_data = not df.empty

        # Save CSV to a temporary file
        temp_dir = get_user_temp_dir()
        unique_filename = f"{uuid.uuid4()}.csv"
        temp_file_path = os.path.join(temp_dir, unique_filename)
        df.to_csv(temp_file_path, index=False)

        # Return all data including the new heatmaps
        return df, unique_filename, insights, bump_chart_name, day_heatmap_name, month_heatmap_name, time_heatmap_name, csv_preview_html, has_valid_data

    except Exception as e:
        logger.exception(f"Error processing Instagram data: {e}")
        raise ValueError("An internal error occurred. Please try again.")