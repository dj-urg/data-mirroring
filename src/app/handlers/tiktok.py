import json
import os
import uuid
import logging
import tempfile
import csv
from typing import List, Dict, Any, Tuple, Optional, Union

import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

from werkzeug.datastructures import FileStorage

from app.utils.file_manager import get_user_temp_dir
from app.utils.file_validation import parse_json_file, safe_save_file, sanitize_for_spreadsheet

# Use 'Agg' backend for headless image generation
matplotlib.use('Agg')

# Configure the logger
FLASK_ENV = os.getenv('FLASK_ENV', 'production')
logging_level = logging.WARNING if FLASK_ENV == 'production' else logging.DEBUG
logging.basicConfig(level=logging_level, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

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

def generate_day_heatmap(day_counts: pd.Series) -> matplotlib.figure.Figure:
    """Generates a heatmap showing TikTok engagement by day of the week."""
    day_count_df = pd.DataFrame({'Day': day_counts.index, 'Count': day_counts.values}).set_index('Day')
    fig, ax = plt.subplots(figsize=(8, 2))
    
    try:
        sns.heatmap(day_count_df.T, annot=True, fmt=".0f", cmap="Blues", ax=ax, cbar=False, linewidths=0, linecolor='none')
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

def generate_time_heatmap(hourly_counts: pd.Series) -> matplotlib.figure.Figure:
    """Generates a heatmap showing TikTok engagement by time of day."""
    hour_count_df = pd.DataFrame({'Hour': hourly_counts.index, 'Count': hourly_counts.values}).set_index('Hour')
    fig, ax = plt.subplots(figsize=(8, 2))
    
    try:
        sns.heatmap(hour_count_df.T, annot=True, fmt=".0f", cmap="Blues", ax=ax, cbar=False, linewidths=0, linecolor='none')
    except ValueError:
        logger.warning("Seaborn heatmap failed, falling back to matplotlib.")
        ax.imshow(hour_count_df.T, cmap="Blues", aspect='auto')
        
    for spine in ax.spines.values(): spine.set_visible(False)
    ax.tick_params(axis='both', which='both', length=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_ylabel("")
    ax.set_xlabel("Hour of Day", fontsize=10)
    ax.grid(False)
    plt.tight_layout()
    return fig

def generate_month_heatmap(df: pd.DataFrame) -> matplotlib.figure.Figure:
    """Generates a heatmap showing TikTok engagement by month."""
    df = df.copy()
    df['month'] = pd.to_datetime(df['timestamp']).dt.month
    df['year'] = pd.to_datetime(df['timestamp']).dt.year
    
    month_counts = df.pivot_table(index='year', columns='month', values='video_title', aggfunc='count', fill_value=0)
    
    month_names = {i: m for i, m in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], 1)}
    month_counts.columns = [month_names.get(m, m) for m in month_counts.columns]
    
    fig, ax = plt.subplots(figsize=(8, 2))
    
    try:
        sns.heatmap(month_counts, annot=True, fmt="d", cmap="Blues", ax=ax, cbar=False, linewidths=0, linecolor='none')
    except ValueError:
        logger.warning("Seaborn heatmap failed, falling back to matplotlib.")
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

# --- Data Processing Functions ---

def parse_tiktok_item(item: Dict[str, Any], source_name: str) -> Optional[Dict[str, Any]]:
    """Extracts relevant fields from a single TikTok video item."""
    try:
        if not isinstance(item, dict): return None
        
        date_str = item.get('Date', '')
        if not date_str: return None
            
        timestamp = pd.to_datetime(date_str, errors='coerce')
        if pd.isnull(timestamp): return None
        
        video_url = item.get('Link', '')
        if video_url and not video_url.startswith(('http://', 'https://')):
            video_url = ''
            
        return {
            'video_title': f"{source_name} Video",
            'video_url': video_url,
            'timestamp': timestamp,
            'source': source_name
        }
    except Exception:
        return None

def process_tiktok_file(files: List[FileStorage]) -> Tuple[pd.DataFrame, str, str, str, Dict, str, str, str, bool, Dict]:
    """Processes multiple TikTok JSON data files and returns insights and plot data."""
    try:
        all_data = []

        sections_to_check = [
            ('Activity', 'Favorite Videos', 'FavoriteVideoList'),
            ('Activity', 'Like List', 'ItemFavoriteList'),
            ('Watch History', 'VideoList'),
            ('Your Activity', 'Watch History', 'VideoList'),
            ('Your Activity', 'Like List', 'ItemFavoriteList')
        ]

        for file in files:
            data, error = parse_json_file(file)
            if error:
                logger.error(f"Failed to parse JSON file: {error}")
                continue

            for section_path in sections_to_check:
                current_level = data
                try:
                    for key in section_path:
                        current_level = current_level.get(key, {})
                    
                    if isinstance(current_level, list):
                        source_name = section_path[-2] if len(section_path) > 2 else 'Unknown Source'
                        for item in current_level:
                            extracted = parse_tiktok_item(item, source_name)
                            if extracted:
                                all_data.append(extracted)
                except Exception:
                    continue

        if not all_data:
            logger.error("No valid video data found.")
            raise ValueError("No valid video data found. Please check the file format.")

        df = pd.DataFrame(all_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Insights
        insights = {
            'total_videos': len(df),
            'time_frame_start': df['timestamp'].min().date() if not df.empty else 'N/A',
            'time_frame_end': df['timestamp'].max().date() if not df.empty else 'N/A'
        }

        # Visualization Data
        df['year'] = df['timestamp'].dt.year
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.day_name()
        
        hour_counts = df['hour'].value_counts().sort_index()
        day_counts = df['day_of_week'].value_counts().reindex(
            ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        )
        
        time_heatmap_name = save_image_temp_file(generate_time_heatmap(hour_counts))
        day_heatmap_name = save_image_temp_file(generate_day_heatmap(day_counts))
        month_heatmap_name = save_image_temp_file(generate_month_heatmap(df))

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
            csv_file_name = os.path.basename(safe_file_path)
            
        if os.path.exists(temp_file_path): os.remove(temp_file_path)
        
        # Excel
        excel_filename = f"{uuid.uuid4()}.xlsx"
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
             file_storage = FileStorage(stream=f, filename=excel_filename, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
             excel_file_path = safe_save_file(file_storage, excel_filename, temp_dir)
             excel_file_name = os.path.basename(excel_file_path)
             
        if os.path.exists(excel_file.name): os.remove(excel_file.name)
        
        # URLs
        url_filename = f"{uuid.uuid4()}.txt"
        urls = df['video_url'].dropna().tolist()
        url_content = '\n'.join([url for url in urls if url and url.strip()])
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(url_content.encode('utf-8'))
            temp_file_path = temp_file.name
            
        with open(temp_file_path, 'rb') as f:
            file_storage = FileStorage(stream=f, filename=url_filename, content_type='text/plain')
            url_file_path = safe_save_file(file_storage, url_filename, temp_dir)
            url_file_name = os.path.basename(url_file_path)
            
        if os.path.exists(temp_file_path): os.remove(temp_file_path)

        preview_data = {
            'columns': df.columns.tolist(),
            'rows': df.head(5).values.tolist()
        }

        # Return: df, csv_file_name, excel_file_name, url_file_name, insights, day_heatmap_name, time_heatmap_name, month_heatmap_name, not df.empty, preview_data
        return df, csv_file_name, excel_file_name, url_file_name, insights, day_heatmap_name, time_heatmap_name, month_heatmap_name, True, preview_data

    except ValueError as e:
        from app.utils.logging_config import log_error_safely
        log_error_safely(e, "TikTok processing ValueError", logger)
        raise ValueError(str(e))
    except Exception as e:
        from app.utils.logging_config import log_error_safely, log_stack_trace_safely
        log_error_safely(e, "TikTok file processing", logger)
        log_stack_trace_safely(e, logger)
        raise ValueError(f"Error processing TikTok data: {str(e)}")
