
import json
import os
import uuid
import logging
import tempfile
from typing import List, Dict, Any, Tuple, Optional, Union

import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
import seaborn as sns
import squarify

from werkzeug.datastructures import FileStorage

from app.utils.file_manager import get_user_temp_dir
from app.utils.file_validation import parse_json_file, safe_save_file, sanitize_for_spreadsheet

# Use 'Agg' backend to avoid GUI issues
matplotlib.use('Agg')

# Configure the logger
FLASK_ENV = os.getenv('FLASK_ENV', 'production')
logging_level = logging.DEBUG if FLASK_ENV == 'development' else logging.WARNING
logging.basicConfig(level=logging_level, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Constants
REQUIRED_COLUMNS = {'timestamp'}

def save_image_temp_file(fig: matplotlib.figure.Figure) -> str:
    """Saves an image in the user's temporary directory and returns the filename."""
    temp_dir = get_user_temp_dir()
    unique_filename = f"{uuid.uuid4()}.png"
    temp_file_path = os.path.join(temp_dir, unique_filename)

    fig.savefig(temp_file_path, bbox_inches='tight')
    plt.close(fig)
    logger.debug(f"Image saved at {temp_file_path}")
    return unique_filename

# --- Visualization Functions ---

def generate_custom_bump_chart(
    channel_ranking: pd.DataFrame,
    title: str = "",
    label_length_limit: int = 25,
    figure_width: float = 18,
    figure_height_scale: float = 0.6
) -> matplotlib.figure.Figure:
    """
    Generate an alluvial diagram with labels showing rank on first appearance.
    """
    if not {'year', 'rank'}.issubset(channel_ranking.columns):
        raise ValueError("DataFrame must contain 'year' and 'rank' columns.")
    
    channel_col = 'channel' if 'channel' in channel_ranking.columns else 'author'
    if channel_col not in channel_ranking.columns:
         raise ValueError("DataFrame must contain either 'channel' or 'author' column.")
         
    has_engagement = 'engagement_count' in channel_ranking.columns

    # Data Preparation
    df = channel_ranking.copy()
    if has_engagement:
        df['engagement_count'] = pd.to_numeric(df['engagement_count'], errors='coerce')
        df['engagement_count'] = df['engagement_count'].fillna(-np.inf)
    
    df['year'] = df['year'].astype(int)
    df['rank'] = df['rank'].astype(int)
    years = sorted(df['year'].unique())
    channels = df[channel_col].unique()

    # Figure Setup
    figure_height = max(8, len(channels) * figure_height_scale)
    fig, ax = plt.subplots(figsize=(figure_width, figure_height), dpi=120)

    # Colors
    cmap = plt.get_cmap("tab20" if len(channels) > 10 else "tab10")
    channel_colors = {channel: cmap(i % cmap.N) for i, channel in enumerate(channels)}

    # Layout Parameters
    node_width = 0.6
    node_spacing = 0.2
    year_spacing = (figure_width - 3) / max(1, len(years) - 1) if len(years) > 1 else 3
    node_height = 0.7
    left_margin = 2.5 

    nodes_by_year_channel = {}

    def draw_flow(start_x, start_y, end_x, end_y, height1, height2, color, alpha=0.6):
        height_factor = 4.0
        cp1_x = start_x + (end_x - start_x) * 0.35
        cp2_x = start_x + (end_x - start_x) * 0.65
        
        top_curve = [
            (start_x, start_y + (height1 / height_factor)), 
            (cp1_x, start_y + (height1 / height_factor)), 
            (cp2_x, end_y + (height2 / height_factor)), 
            (end_x, end_y + (height2 / height_factor))
        ]
        bottom_curve = [
            (end_x, end_y - (height2 / height_factor)), 
            (cp2_x, end_y - (height2 / height_factor)), 
            (cp1_x, start_y - (height1 / height_factor)), 
            (start_x, start_y - (height1 / height_factor))
        ]
        
        verts = top_curve + bottom_curve + [(start_x, start_y + (height1 / height_factor))]
        codes = [Path.MOVETO] + [Path.CURVE4] * 3 + [Path.LINETO] + [Path.CURVE4] * 3 + [Path.CLOSEPOLY]
        path = Path(verts, codes)
        patch = patches.PathPatch(path, facecolor=color, alpha=alpha, edgecolor='none', lw=0)
        ax.add_patch(patch)

    # Draw Nodes
    max_nodes_in_year = 0
    for year_idx, year in enumerate(years):
        x_pos = left_margin + year_idx * year_spacing
        year_data = df[df['year'] == year].copy()

        sort_col = 'engagement_count' if has_engagement else 'rank'
        ascending_sort = False if has_engagement else True
        year_data = year_data.sort_values(sort_col, ascending=ascending_sort)
        year_data.reset_index(drop=True, inplace=True)

        max_nodes_in_year = max(max_nodes_in_year, len(year_data))

        for i, row in year_data.iterrows():
            channel = row[channel_col]
            if pd.isna(channel): continue

            max_items = len(year_data)
            y_pos = (max_items - 1 - i) * (node_height + node_spacing)
            node_color = channel_colors.get(channel, 'grey')

            rect = patches.Rectangle(
                (x_pos, y_pos), node_width, node_height,
                facecolor=node_color, edgecolor='white', linewidth=0.5, alpha=0.9
            )
            ax.add_patch(rect)

            # Label
            name_part = str(channel)
            if len(name_part) > (label_length_limit - 5):
                name_part = name_part[:label_length_limit-8] + "..."
            
            ax.text(
                x_pos + node_width / 2,
                y_pos + node_height + 0.05,
                name_part,
                va='bottom', ha='center', fontsize=7, fontweight='normal', color='black'
            )

            # Engagement Count
            if has_engagement and row['engagement_count'] != -np.inf:
                engagement_count = int(row['engagement_count'])
                ax.text(
                    x_pos + node_width / 2, y_pos + node_height / 2, f"{engagement_count:,}",
                    va='center', ha='center', fontsize=8, fontweight='bold', color='black'
                )

            nodes_by_year_channel[(year, channel)] = (x_pos, y_pos, node_height)

    # Draw Connections
    for channel in channels:
        if pd.isna(channel): continue
        channel_data = df[df[channel_col] == channel]
        channel_years = sorted(channel_data['year'].unique())
        for i in range(len(channel_years) - 1):
            year1, year2 = channel_years[i], channel_years[i+1]
            if (year1, channel) in nodes_by_year_channel and (year2, channel) in nodes_by_year_channel:
                node1_x, node1_y, node1_h = nodes_by_year_channel[(year1, channel)]
                node2_x, node2_y, node2_h = nodes_by_year_channel[(year2, channel)]
                draw_flow(node1_x + node_width, node1_y + node1_h / 2, node2_x, node2_y + node2_h / 2, 
                          node1_h, node2_h, channel_colors.get(channel, 'grey'), alpha=0.5)

    # Year Labels
    for year_idx, year in enumerate(years):
        ax.text(
            left_margin + year_idx * year_spacing + node_width / 2, -0.5, str(year),
            ha='center', va='top', fontsize=11, fontweight='bold', color='black'
        )

    # Settings
    right_limit = left_margin + (len(years) - 1) * year_spacing + node_width + 1.0
    ax.set_xlim(0, right_limit)
    ax.set_ylim(-1.0, max_nodes_in_year * (node_height + node_spacing) + 0.5)
    ax.set_title(title, fontsize=16, fontweight='bold', pad=25, color='black')
    ax.set_axis_off()
    fig.tight_layout(rect=[0.02, 0.05, 0.98, 0.95])
    return fig

def generate_heatmap(df: pd.DataFrame) -> Optional[matplotlib.figure.Figure]:
    """Generates a heatmap showing Instagram engagement by day of the week with no grid lines."""
    if 'timestamp' not in df.columns:
        logger.warning("Timestamp column not found in the DataFrame.")
        return None

    # Prepare Data
    df = df.copy() # Avoid modifying original
    df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.day_name()
    day_counts = df['day_of_week'].value_counts().reindex(
        ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    )
    
    # Create DataFrame for plotting
    day_count_df = pd.DataFrame({'Day': day_counts.index, 'Count': day_counts.values}).set_index('Day')

    fig, ax = plt.subplots(figsize=(8, 2))
    
    try:
        # Try using seaborn first, but with error handling for known compatibility issues
        sns.heatmap(
            day_count_df.T,
            annot=True,
            fmt="d",
            cmap="Blues",
            ax=ax,
            cbar=False,
            linewidths=0,
            linecolor='none'
        )
    except ValueError:
        # Fallback to pure matplotlib if seaborn fails (common with strict versioning)
        logger.warning("Seaborn heatmap failed, falling back to matplotlib.")
        data = day_count_df.T.values
        im = ax.imshow(data, cmap="Blues", aspect='auto')
        
        # Add text annotations
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                val = data[i, j]
                if not np.isnan(val):
                    ax.text(j, i, str(int(val)), ha="center", va="center", color="black")
                    
        # Set ticks
        ax.set_xticks(np.arange(len(day_count_df.index)))
        ax.set_xticklabels(day_count_df.index)
        ax.set_yticks([])

    # Visual Cleanup
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(axis='both', which='both', length=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_ylabel("")
    ax.set_xlabel("")
    ax.grid(False)
    plt.tight_layout()
    return fig

def generate_month_heatmap(df: pd.DataFrame) -> matplotlib.figure.Figure:
    """Generates a heatmap showing Instagram engagement by month."""
    df = df.copy()
    df['month'] = pd.to_datetime(df['timestamp']).dt.month
    df['year'] = pd.to_datetime(df['timestamp']).dt.year
    
    month_counts = df.pivot_table(
        index='year', columns='month', values='title', aggfunc='count', fill_value=0
    )
    
    month_names = {i: datetime_month for i, datetime_month in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], 1)}
    month_counts.columns = [month_names.get(m, m) for m in month_counts.columns]
    
    fig, ax = plt.subplots(figsize=(10, max(2, len(month_counts) * 0.6)))
    
    try:
        sns.heatmap(
            month_counts, annot=True, fmt="d", cmap="Blues", ax=ax, cbar=False,
            linewidths=0, linecolor='none', annot_kws={"size": 10}
        )
    except ValueError:
        # Fallback for compatibility
        logger.warning("Seaborn month heatmap failed, falling back to matplotlib.")
        ax.imshow(month_counts, cmap="Blues", aspect='auto')
    
    for spine in ax.spines.values(): spine.set_visible(False)
    ax.tick_params(axis='both', which='both', length=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_ylabel("")
    ax.set_xlabel("")
    ax.tick_params(labelsize=11)
    ax.grid(False)
    plt.tight_layout(pad=0.5)
    return fig

def generate_time_of_day_heatmap(df: pd.DataFrame) -> Optional[matplotlib.figure.Figure]:
    """Generates a heatmap showing Instagram engagement by time of day."""
    if 'timestamp' not in df.columns or not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        logger.warning("Timestamp column is not in datetime format for time of day analysis.")
        return None
        
    df_with_hour = df.copy()
    df_with_hour['hour'] = df_with_hour['timestamp'].dt.hour
    
    time_ranges = {
        h: '12-4 AM' if 0 <= h < 4 else
           '4-8 AM' if 4 <= h < 8 else
           '8-12 PM' if 8 <= h < 12 else
           '12-4 PM' if 12 <= h < 16 else
           '4-8 PM' if 16 <= h < 20 else
           '8-12 AM'
        for h in range(24)
    }
    
    df_with_hour['time_range'] = df_with_hour['hour'].map(time_ranges)
    time_range_counts = df_with_hour['time_range'].value_counts().reindex([
        '12-4 AM', '4-8 AM', '8-12 PM', '12-4 PM', '4-8 PM', '8-12 AM'
    ])
    
    hour_count_df = pd.DataFrame({'Time': time_range_counts.index, 'Count': time_range_counts.values}).set_index('Time')
    
    fig, ax = plt.subplots(figsize=(8, 2))
    
    try:
        sns.heatmap(
            hour_count_df.T, annot=True, fmt=".0f", cmap="Blues", ax=ax, cbar=False,
            linewidths=0, linecolor='none'
        )
    except ValueError:
        ax.imshow(hour_count_df.T, cmap="Blues", aspect='auto')

    for spine in ax.spines.values(): spine.set_visible(False)
    ax.tick_params(axis='both', which='both', length=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_ylabel("")
    ax.set_xlabel("")
    ax.grid(False)
    plt.tight_layout()
    return fig

def generate_author_treemap(df: pd.DataFrame) -> matplotlib.figure.Figure:
    """Generates a treemap of top authors based on engagement count."""
    authors_df = df[df['author'] != 'Unknown']
    
    if authors_df.empty:
        author_data = df.groupby('category').size().reset_index(name='count')
        author_data.columns = ['author', 'count']
    else:
        author_data = authors_df.groupby('author').size().reset_index(name='count')
    
    author_data = author_data.sort_values('count', ascending=False).head(15)
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    if not author_data.empty:
        sizes = author_data['count'].values
        labels = [f"{author}\n({count})" if len(author) < 15 else f"{author[:12]}...\n({count})" 
                  for author, count in zip(author_data['author'], author_data['count'])]
        
        cmap = plt.get_cmap('Blues')
        norm = plt.Normalize(min(sizes), max(sizes))
        colors = [cmap(norm(size)) for size in sizes]
        
        squarify.plot(sizes=sizes, label=labels, color=colors, alpha=0.8, ax=ax)
    
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values(): spine.set_visible(False)
    ax.set_title("", fontsize=14)
    plt.tight_layout()
    return fig

# --- Data Processing Functions ---

def parse_instagram_item(item: Dict[str, Any], category: str) -> Optional[Dict[str, Any]]:
    """Extracts timestamp, author, etc. from a single Instagram JSON item."""
    timestamp = None
    href = "N/A"
    author = "Unknown"

    try:
        if category == 'Saved Media':
            if 'string_map_data' in item:
                saved_on = item['string_map_data'].get('Saved on', {})
                timestamp = saved_on.get('timestamp')
                href = saved_on.get('href', '')
                author = item.get('title', 'Unknown')
        
        elif category in ['Liked Media']:
            if 'string_list_data' in item and item['string_list_data']:
                data_point = item['string_list_data'][0]
                timestamp = data_point.get('timestamp')
                href = data_point.get('href', '')
                author = item.get('title', 'No Title')
                if author == 'No Title': author = 'Unknown'

        elif category in ['Posts Seen', 'Videos Watched']:
            if 'string_map_data' in item:
                map_data = item['string_map_data']
                timestamp = map_data.get('Time', {}).get('timestamp')
                author = map_data.get('Author', {}).get('value', 'Unknown')

        elif category == 'Chaining Seen':
            if 'string_list_data' in item and item['string_list_data']:
                timestamp = item['string_list_data'][0].get('timestamp')

        if timestamp is None:
            return None

        # Convert timestamp
        try:
            ts_dt = pd.to_datetime(timestamp, unit='s', errors='coerce')
            if pd.isna(ts_dt): return None
        except ValueError:
            return None

        return {
            'title': item.get('title', 'No Title'),
            'href': href,
            'timestamp': ts_dt,
            'category': category,
            'author': author
        }
    except Exception:
        return None

def process_instagram_file(files: List[FileStorage]) -> Tuple[pd.DataFrame, str, Dict, str, str, str, Optional[str], Dict, bool]:
    """Processes Instagram JSON data, extracts insights, and generates visualizations."""
    try:
        logger.info(f"Processing {len(files) if files else 0} Instagram file(s)")
        
        all_data = []
        
        category_map = {
            'saved_saved_media': 'Saved Media',
            'likes_media_likes': 'Liked Media',
            'impressions_history_posts_seen': 'Posts Seen',
            'impressions_history_chaining_seen': 'Chaining Seen',
            'impressions_history_videos_watched': 'Videos Watched'
        }

        for file in files:
            file_name = getattr(file, 'filename', 'unknown')
            data, error = parse_json_file(file)
            
            if error:
                logger.warning(f"Failed to parse JSON file {file_name}: {error}")
                continue

            for key, category in category_map.items():
                if key in data:
                    for item in data[key]:
                        extracted = parse_instagram_item(item, category)
                        if extracted:
                            all_data.append(extracted)

        if not all_data:
            logger.warning("No valid data found in uploaded Instagram files.")
            return pd.DataFrame(), "", {}, "", "", "", None, {}, False

        # Create DataFrame
        df = pd.DataFrame(all_data)
        
        # Keep copy with datetime objects for time-of-day analysis
        df_with_time = df.copy()

        # Convert timestamp to date for main analysis (was overwriting 'timestamp' before)
        df['analysis_date'] = pd.to_datetime(df['timestamp']).dt.date
        df = df.dropna(subset=['analysis_date'])

        if df.empty:
             return pd.DataFrame(), "", {}, "", "", "", None, {}, False

        # Insights
        insights = {
            'total_entries': len(df),
            'time_frame_start': df['analysis_date'].min(),
            'time_frame_end': df['analysis_date'].max(),
            'videos_watched': len(df[df['category'] == 'Videos Watched']),
            'unique_authors': df['author'].nunique()
        }

        # Visualize
        # Bump Chart preparation
        # Use 'analysis_date' for year extraction instead of 'timestamp'
        df['year'] = pd.to_datetime(df['analysis_date']).dt.year
        authors_df = df[df['author'] != 'Unknown']
        
        if authors_df.empty:
            # Fallback
            author_data = df.groupby(['year', 'category']).size().reset_index(name='engagement_count')
            bump_data = author_data.groupby('year').apply(lambda x: x.nlargest(5, 'engagement_count')).reset_index(drop=True)
            bump_data['rank'] = bump_data.groupby('year')['engagement_count'].rank(ascending=False, method='first')
            bump_data = bump_data.rename(columns={'category': 'author'})
        else:
            author_data = authors_df.groupby(['year', 'author']).size().reset_index(name='engagement_count')
            bump_data = author_data.groupby('year').apply(lambda x: x.nlargest(5, 'engagement_count')).reset_index(drop=True)
            bump_data['rank'] = bump_data.groupby('year')['engagement_count'].rank(ascending=False, method='first')

        if len(bump_data) > 0 and len(bump_data['year'].unique()) > 1:
            bump_fig = generate_custom_bump_chart(bump_data)
            bump_chart_name = save_image_temp_file(bump_fig)
        else:
            treemap_fig = generate_author_treemap(df)
            bump_chart_name = save_image_temp_file(treemap_fig)

        # Heatmaps
        day_heatmap_name = save_image_temp_file(generate_heatmap(df)) if not df.empty else ""
        month_heatmap_name = save_image_temp_file(generate_month_heatmap(df)) if not df.empty else ""
        time_heatmap_name = save_image_temp_file(generate_time_of_day_heatmap(df_with_time)) if not df_with_time.empty else None

        # Preview Data
        preview_data = {
            'columns': df.columns.tolist(),
            'rows': df.head(5).values.tolist()
        }

        # CSV Export
        df_csv = df.copy()
        
        # Add Unix timestamp ONLY for export
        if 'timestamp' in df_csv.columns:
             df_csv['unix_timestamp'] = df_csv['timestamp'].astype('int64') // 10**9
             
        for col in df_csv.select_dtypes(include=['object']):
            df_csv[col] = df_csv[col].apply(sanitize_for_spreadsheet)
            
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
            temp_file.write(df_csv.to_csv(index=False).encode('utf-8'))
            temp_file_path = temp_file.name
            os.chmod(temp_file_path, 0o600)
            
        unique_filename = f"{uuid.uuid4()}.csv"
        temp_dir = get_user_temp_dir()
        
        with open(temp_file_path, 'rb') as f:
            file_storage = FileStorage(stream=f, filename=unique_filename, content_type='text/csv')
            safe_save_file(file_storage, unique_filename, temp_dir)
            
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        return df, unique_filename, insights, bump_chart_name, day_heatmap_name, month_heatmap_name, time_heatmap_name, preview_data, True

    except Exception as e:
        logger.exception(f"Error processing Instagram data: {e}")
        raise ValueError("An internal error occurred. Please try again.")
