
import json
import os
import uuid
import logging
import tempfile
import csv
from typing import List, Dict, Any, Tuple, Optional, Union

import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
import seaborn as sns

from werkzeug.datastructures import FileStorage

from app.utils.file_manager import get_user_temp_dir
from app.utils.file_validation import parse_json_file, safe_save_file, sanitize_for_spreadsheet

# Use 'Agg' backend to avoid GUI issues
matplotlib.use('Agg')

# Configure the logger
FLASK_ENV = os.getenv('FLASK_ENV', 'production')
logging_level = logging.DEBUG if FLASK_ENV == 'development' else logging.WARNING
logging.basicConfig(level=logging_level, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def save_image_temp_file(fig: matplotlib.figure.Figure) -> str:
    """Saves an image in the user's temporary directory and returns the filename."""
    temp_dir = get_user_temp_dir()
    unique_filename = f"{uuid.uuid4()}.png"
    temp_file_path = os.path.join(temp_dir, unique_filename)

    fig.savefig(temp_file_path, 
                bbox_inches='tight',
                dpi=100,
                format='png',
                transparent=False,
                pad_inches=0.1)
    
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
    Adapted from Instagram handler for visual consistency.
    """
    if not {'year', 'rank'}.issubset(channel_ranking.columns):
        raise ValueError("DataFrame must contain 'year' and 'rank' columns.")
    
    # YouTube specific adaptation: use 'view_counts' as 'engagement_count' logic
    has_engagement = 'view_counts' in channel_ranking.columns
    channel_col = 'channel'

    # Data Preparation
    df = channel_ranking.copy()
    if has_engagement:
        df['view_counts'] = pd.to_numeric(df['view_counts'], errors='coerce')
        df['view_counts'] = df['view_counts'].fillna(-np.inf)
    
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

        # YouTube: Sort by view_counts if available, else rank
        sort_col = 'view_counts' if has_engagement else 'rank'
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

            # View Count (Engagement)
            if has_engagement and row['view_counts'] != -np.inf:
                count_val = int(row['view_counts'])
                ax.text(
                    x_pos + node_width / 2, y_pos + node_height / 2, f"{count_val:,}",
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

def generate_heatmap(day_counts: pd.Series) -> matplotlib.figure.Figure:
    """Generates a heatmap showing YouTube engagement by day of the week."""
    day_count_df = pd.DataFrame({'Day': day_counts.index, 'Count': day_counts.values}).set_index('Day')
    fig, ax = plt.subplots(figsize=(8, 2))
    
    try:
        sns.heatmap(
            day_count_df.T, annot=True, fmt=".0f", cmap="Blues", ax=ax, cbar=False,
            linewidths=0, linecolor='none'
        )
    except ValueError:
        logger.warning("Seaborn heatmap failed, falling back to matplotlib.")
        ax.imshow(day_count_df.T, cmap="Blues", aspect='auto')

    for spine in ax.spines.values(): spine.set_visible(False)
    ax.tick_params(axis='both', which='both', length=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_ylabel("")
    ax.set_xlabel("")
    ax.grid(False)
    plt.tight_layout()
    return fig

def generate_month_heatmap(df: pd.DataFrame) -> matplotlib.figure.Figure:
    """Generates a heatmap showing YouTube engagement by month."""
    df = df.copy()
    df['month'] = pd.to_datetime(df['timestamp']).dt.month
    df['year'] = pd.to_datetime(df['timestamp']).dt.year
    
    month_counts = df.pivot_table(
        index='year', columns='month', values='video_title', aggfunc='count', fill_value=0
    )
    
    month_names = {i: m for i, m in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], 1)}
    month_counts.columns = [month_names.get(m, m) for m in month_counts.columns]
    
    fig, ax = plt.subplots(figsize=(8, 2))
    
    try:
        sns.heatmap(
            month_counts, annot=True, fmt=".0f", cmap="Blues", ax=ax, cbar=False,
            linewidths=0, linecolor='none'
        )
    except ValueError:
        ax.imshow(month_counts, cmap="Blues", aspect='auto')
    
    for spine in ax.spines.values(): spine.set_visible(False)
    ax.tick_params(axis='both', which='both', length=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_ylabel("Year", fontsize=10)
    ax.set_xlabel("Month", fontsize=10)
    ax.set_title("")
    ax.grid(False)
    plt.tight_layout()
    return fig

def generate_time_of_day_heatmap(df: pd.DataFrame) -> Optional[matplotlib.figure.Figure]:
    """Generates a heatmap showing YouTube engagement by time of day."""
    if 'timestamp' not in df.columns or not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        return None
        
    df = df.copy()
    df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
    
    time_ranges = {
        h: '12-4 AM' if 0 <= h < 4 else
           '4-8 AM' if 4 <= h < 8 else
           '8-12 PM' if 8 <= h < 12 else
           '12-4 PM' if 12 <= h < 16 else
           '4-8 PM' if 16 <= h < 20 else
           '8-12 AM'
        for h in range(24)
    }
    
    df['time_range'] = df['hour'].map(time_ranges)
    time_range_counts = df['time_range'].value_counts().reindex([
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
    ax.set_xlabel("Time of Day", fontsize=10)
    ax.grid(False)
    plt.tight_layout()
    return fig

# --- Data Processing Functions ---

def parse_youtube_item(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extracts relevant fields from a single YouTube watch history item."""
    try:
        if not isinstance(item, dict):
            return None
            
        # Parse timestamp
        time_str = item.get('time', '')
        timestamp = pd.to_datetime(time_str, errors='coerce')
        if pd.isnull(timestamp):
            return None
            
        # Parse Subtitles (Channel)
        subtitles = item.get('subtitles', [{}])
        if not isinstance(subtitles, list): subtitles = [{}]
        subtitle_name = subtitles[0].get('name', 'Unknown') if subtitles else 'Unknown'
        subtitle_url = subtitles[0].get('url', '') if subtitles else ''
        if subtitle_url and not subtitle_url.startswith(('http://', 'https://')):
             subtitle_url = ''
             
        # Parse Title
        video_title = item.get('title', 'No Title')
        if not isinstance(video_title, str): video_title = 'No Title'
        video_url = item.get('titleUrl', '')
        if video_url and not video_url.startswith(('http://', 'https://')):
            video_url = ''
            
        return {
            'video_title': video_title,
            'video_url': video_url,
            'timestamp': timestamp,
            'channel': subtitle_name,
            'channel_url': subtitle_url
        }
    except Exception:
        return None

def process_youtube_file(files: List[FileStorage]) -> Tuple[pd.DataFrame, str, str, Dict, str, str, str, Optional[str], bool, Dict]:
    """Processes multiple YouTube JSON data files and returns insights and plot data."""
    try:
        all_data = []

        for file in files:
            data, error = parse_json_file(file)
            if error:
                logger.warning(f"Failed to parse YouTube JSON file: {error}")
                continue
                
            if isinstance(data, list):
                for item in data:
                    extracted = parse_youtube_item(item)
                    if extracted:
                        all_data.append(extracted)

        if not all_data:
            logger.warning("No valid data found in uploaded YouTube files")
            raise ValueError("No valid data found in the uploaded files.")

        df = pd.DataFrame(all_data)
        
        # Insights
        insights = {
            'total_videos': len(df),
            'time_frame_start': df['timestamp'].min().date() if not df.empty else 'N/A',
            'time_frame_end': df['timestamp'].max().date() if not df.empty else 'N/A',
        }

        # Visualization Data Preparation
        df['year'] = pd.to_datetime(df['timestamp']).dt.year
        df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.day_name()
        
        day_counts = df['day_of_week'].value_counts().reindex(
            ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        )
        
        # Bump Chart Data
        channel_data = df.groupby(['year', 'channel']).size().reset_index(name='view_counts')
        channel_data = channel_data[channel_data['channel'] != 'Unknown']
        
        if not channel_data.empty:
            top_channels_per_year = channel_data.groupby('year').apply(lambda x: x.nlargest(5, 'view_counts')).reset_index(drop=True)
            top_channels_per_year['rank'] = top_channels_per_year.groupby('year')['view_counts'].rank(ascending=False, method='first')
            bump_chart_name = save_image_temp_file(generate_custom_bump_chart(top_channels_per_year))
        else:
            bump_chart_name = "" # Handle case with no valid channel data

        # Heatmaps
        day_heatmap_name = save_image_temp_file(generate_heatmap(day_counts))
        month_heatmap_name = save_image_temp_file(generate_month_heatmap(df))
        time_heatmap_name = save_image_temp_file(generate_time_of_day_heatmap(df))

        # Exports
        unique_filename = f"{uuid.uuid4()}.csv"
        temp_dir = get_user_temp_dir()
        
        # CSV
        df_csv = df.copy()
        for col in df_csv.select_dtypes(include=['object']):
             df_csv[col] = df_csv[col].apply(sanitize_for_spreadsheet)
             
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
            temp_file.write(df_csv.to_csv(index=False, quoting=csv.QUOTE_ALL, encoding='utf-8').encode('utf-8'))
            temp_file_path = temp_file.name
            os.chmod(temp_file_path, 0o600)
            
        with open(temp_file_path, 'rb') as f:
            file_storage = FileStorage(stream=f, filename=unique_filename, content_type='text/csv')
            safe_file_path = safe_save_file(file_storage, unique_filename, temp_dir)
            unique_filename = os.path.basename(safe_file_path)
            
        if os.path.exists(temp_file_path): os.remove(temp_file_path)
        
        # Excel
        excel_filename_uuid = f"{uuid.uuid4()}.xlsx"
        excel_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        excel_file.close()

        df_excel = df.copy()
        for col in df_excel.select_dtypes(include=['datetime64[ns, UTC]']).columns:
            df_excel[col] = df_excel[col].dt.tz_localize(None)
        df_excel.replace(r'\n', ' ', regex=True, inplace=True)
         
        for col in df_excel.select_dtypes(include=['object']):
             df_excel[col] = df_excel[col].apply(sanitize_for_spreadsheet)
             
        df_excel.to_excel(excel_file.name, index=False, engine='openpyxl')
        
        with open(excel_file.name, 'rb') as f:
             file_storage = FileStorage(stream=f, filename=excel_filename_uuid, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
             excel_file_path = safe_save_file(file_storage, excel_filename_uuid, temp_dir)
             excel_filename = os.path.basename(excel_file_path)
             
        if os.path.exists(excel_file.name): os.remove(excel_file.name)
        
        preview_data = {
            'columns': df.columns.tolist(),
            'rows': df.head(5).values.tolist()
        }

        return df, excel_filename, unique_filename, insights, bump_chart_name, day_heatmap_name, month_heatmap_name, time_heatmap_name, True, preview_data

    except ValueError as e:
        logger.warning(f"ValueError in YouTube processing: {str(e)}")
        raise ValueError(str(e))
    except Exception as e:
        logger.exception(f"Error processing YouTube data: {e}")
        raise ValueError("An internal error occurred. Please try again.")
