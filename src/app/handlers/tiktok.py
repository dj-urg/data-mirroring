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
from app.utils.file_manager import get_user_temp_dir
from app.utils.file_validation import parse_json_file, safe_save_file, sanitize_for_spreadsheet
from app.utils.file_validation import safe_save_file
from werkzeug.datastructures import FileStorage
import tempfile
import csv
import openpyxl

# Use 'Agg' backend for headless image generation
matplotlib.use('Agg')

# Configure the logger
FLASK_ENV = os.getenv('FLASK_ENV', 'production')

if FLASK_ENV == 'production':
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(levelname)s: %(message)s')
else:
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

logger = logging.getLogger()

# Helper function to save images as temporary files
def save_image_temp_file(fig):
    """Saves an image in the user's temporary directory and returns the filename."""
    temp_dir = get_user_temp_dir()
    unique_filename = f"{uuid.uuid4()}.png"
    temp_file_path = os.path.join(temp_dir, unique_filename)

    fig.savefig(temp_file_path, bbox_inches='tight')
    plt.close(fig)  # Free up memory
    logger.debug(f"Image saved at {temp_file_path}")
    return unique_filename  # Return just the filename

# Helper function to save CSV as a temporary file
def save_csv_temp_file(df):
    """Saves CSV data in the user's temporary directory and returns the filename."""
    temp_dir = get_user_temp_dir()
    unique_filename = f"{uuid.uuid4()}.csv"
    temp_file_path = os.path.join(temp_dir, unique_filename)
    
    # Replace all newline characters in the DataFrame (avoid breaking CSV format when opening in Excel)
    df.replace(r'\n', ' ', regex=True, inplace=True)

    # Sanitize data to prevent formula injection
    for col in df.select_dtypes(include=['object']):
        df[col] = df[col].apply(sanitize_for_spreadsheet)

    df.to_csv(temp_file_path, index=False, quoting=csv.QUOTE_ALL, encoding='utf-8')
    os.chmod(temp_file_path, 0o600)  # Secure file permissions
    logger.debug(f"CSV saved at {temp_file_path}")
    return unique_filename  # Return just the filename

def save_excel_temp_file(df):
    """Saves Excel data in the user's temporary directory and returns the filename."""
    temp_dir = get_user_temp_dir()
    unique_filename = f"{uuid.uuid4()}.xlsx"
    temp_file_path = os.path.join(temp_dir, unique_filename)

    # Create a copy of the DataFrame to avoid modifying the original
    excel_df = df.copy()
    
    # Convert timezone-aware datetime columns to timezone-naive
    for col in excel_df.select_dtypes(include=['datetime64[ns, UTC]']).columns:
        excel_df[col] = excel_df[col].dt.tz_localize(None)
    
    # Replace newline characters to ensure proper formatting in Excel
    excel_df.replace(r'\n', ' ', regex=True, inplace=True)

    # Sanitize data to prevent formula injection
    for col in excel_df.select_dtypes(include=['object']):
        excel_df[col] = excel_df[col].apply(sanitize_for_spreadsheet)

    # Save the DataFrame as an Excel file
    excel_df.to_excel(temp_file_path, index=False, engine='openpyxl')
    os.chmod(temp_file_path, 0o600)  # Secure file permissions
    logger.debug(f"Excel file saved at {temp_file_path}")
    return unique_filename  # Return just the filename

def save_urls_temp_file(df):
    """Saves video URLs in the user's temporary directory and returns the filename."""
    temp_dir = get_user_temp_dir()
    unique_filename = f"{uuid.uuid4()}.txt"
    temp_file_path = os.path.join(temp_dir, unique_filename)
    
    # Filter out empty URLs and write to file
    urls = df['video_url'].dropna().tolist()
    with open(temp_file_path, 'w', encoding='utf-8') as f:
        for url in urls:
            if url and url.strip():  # Check if URL is not empty
                f.write(f"{url}\n")
    
    os.chmod(temp_file_path, 0o600)  # Secure file permissions
    logger.debug(f"URL list saved at {temp_file_path}")
    return unique_filename  # Return just the filename

# Generate heatmap for TikTok activity by day of week
def generate_day_heatmap(day_counts):
    """Generates a heatmap showing TikTok engagement by day of the week with no grid lines."""
    # Convert day counts to a dataframe
    day_count_df = pd.DataFrame({'Day': day_counts.index, 'Count': day_counts.values}).set_index('Day')
    
    # Create a heatmap
    fig, ax = plt.subplots(figsize=(8, 2))
    
    # Create heatmap with all grid lines removed
    sns.heatmap(
        day_count_df.T, 
        annot=True, 
        fmt=".0f",  # Use float format that shows no decimal places
        cmap="Blues", 
        ax=ax, 
        cbar=False,
        linewidths=0,
        linecolor='none'
    )
    
    # Remove all spines
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    # Turn off axis ticks
    ax.tick_params(axis='both', which='both', length=0)
    
    # Clear the top and right spines specifically
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

# Generate heatmap for TikTok activity by hour of day
def generate_time_heatmap(hourly_counts):
    """Generates a heatmap showing TikTok engagement by time of day with no grid lines."""
    # Create the dataframe for the heatmap
    hour_count_df = pd.DataFrame({'Hour': hourly_counts.index, 'Count': hourly_counts.values}).set_index('Hour')
    
    # Create figure and axes
    fig, ax = plt.subplots(figsize=(8, 2))
    
    # Create heatmap with all grid lines removed
    sns.heatmap(
        hour_count_df.T, 
        annot=True, 
        fmt=".0f",  # Use float format that shows no decimal places
        cmap="Blues", 
        ax=ax, 
        cbar=False,
        linewidths=0,
        linecolor='none'
    )
    
    # Remove all spines
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    # Turn off axis ticks
    ax.tick_params(axis='both', which='both', length=0)
    
    # Clear the top and right spines specifically
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Keep axis labels empty
    ax.set_ylabel("")
    ax.set_xlabel("Hour of Day", fontsize=10)
    
    # Turn off all grid lines
    ax.grid(False)
    
    plt.tight_layout()
    return fig

# Generate heatmap for TikTok activity by month
def generate_month_heatmap(df):
    """Generates a heatmap showing TikTok engagement by month."""
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
        annot=True,
        fmt="d",
        cmap="Blues",
        ax=ax,
        cbar=False,
        linewidths=0,
        linecolor='none'
    )
    
    # Remove all spines
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    # Turn off axis ticks
    ax.tick_params(axis='both', which='both', length=0)
    
    # Clear the top and right spines specifically
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

# Main processing function for TikTok files
def process_tiktok_file(files):
    try:
        all_data = []

        for file in files:
            try:
                
                data, error = parse_json_file(file)
                if error:
                    logger.error(f"Failed to parse JSON file: {error}")
                    raise ValueError(f"Invalid JSON file: {error}. Please upload a valid TikTok data file.")
                
                # Log the top-level keys in the JSON
                logger.info(f"Top-level keys in JSON: {list(data.keys())}")
            except ValueError as e:
                # Re-raise ValueError with our custom message
                raise ValueError(f"Invalid JSON file: {str(e)}. Please upload a valid TikTok data file.")
            except Exception as e:
                logger.error(f"Error parsing file: {type(e).__name__} - {str(e)}")
                raise ValueError("Invalid JSON file. Please upload a valid TikTok data file.")

            # Check multiple possible locations for video data
            sections_to_check = [
                ('Activity', 'Favorite Videos', 'FavoriteVideoList'),
                ('Activity', 'Like List', 'ItemFavoriteList'),
                ('Watch History', 'VideoList'),
                ('Your Activity', 'Watch History', 'VideoList'),
                ('Your Activity', 'Like List', 'ItemFavoriteList')
            ]

            for section_path in sections_to_check:
                current_level = data
                try:
                    for key in section_path:
                        current_level = current_level.get(key, {})
                    
                    # If we've found a list of videos
                    if isinstance(current_level, list):
                        source_name = section_path[-2] if len(section_path) > 2 else 'Unknown Source'
                        logger.info(f"Found {len(current_level)} videos in {source_name}")
                        
                        for item in current_level:
                            try:
                                # Validate item structure
                                if not isinstance(item, dict):
                                    logger.warning(f"Skipping non-dict item: {type(item)}")
                                    continue
                                
                                # Extract and validate date
                                date_str = item.get('Date', '')
                                if not date_str:
                                    logger.warning("Skipping item with missing date")
                                    continue
                                    
                                timestamp = pd.to_datetime(date_str, errors='coerce')
                                
                                # Skip if timestamp is invalid
                                if pd.isnull(timestamp):
                                    logger.warning(f"Skipping item with invalid timestamp: {date_str}")
                                    continue
                                
                                # Safely extract video URL with validation
                                video_url = item.get('Link', '')
                                if video_url:
                                    # Basic URL validation
                                    if not video_url.startswith(('http://', 'https://')):
                                        video_url = ''  # Clear invalid URLs
                                
                                all_data.append({
                                    'video_title': f"{source_name} Video",
                                    'video_url': video_url,
                                    'timestamp': timestamp,
                                    'source': source_name
                                })
                            except Exception as e:
                                logger.warning(f"Error processing video item: {e}")
                except Exception as e:
                    logger.warning(f"Error checking section {section_path}: {e}")

        # Log total data found
        logger.info(f"Total videos processed: {len(all_data)}")
        
        if not all_data:
            # Log more detailed error information
            logger.error("No valid video data found. JSON structure may be different from expected.")
            raise ValueError("No valid video data found. Please check the file format.")

        # Create DataFrame from collected data
        df = pd.DataFrame(all_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Generate insights
        insights = {
            'total_videos': len(df),
            'time_frame_start': df['timestamp'].min().date() if not df.empty else 'N/A',
            'time_frame_end': df['timestamp'].max().date() if not df.empty else 'N/A'
        }

        # Prepare data for visualizations
        df['year'] = df['timestamp'].dt.year
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.day_name()
        
        # Count videos by hour of day
        hour_counts = df['hour'].value_counts().sort_index()
        
        # Count videos by day of week
        day_counts = df['day_of_week'].value_counts().reindex(
            ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        )
        
        # Generate visualizations
        time_heatmap_name = save_image_temp_file(generate_time_heatmap(hour_counts))
        day_heatmap_name = save_image_temp_file(generate_day_heatmap(day_counts))
        month_heatmap_name = save_image_temp_file(generate_month_heatmap(df))
        
        # Save CSV data securely
        # Sanitize data to prevent formula injection
        for col in df.select_dtypes(include=['object']):
            df[col] = df[col].apply(sanitize_for_spreadsheet)
            
        csv_content = df.to_csv(index=False, quoting=csv.QUOTE_ALL, encoding='utf-8')
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
            temp_file.write(csv_content.encode('utf-8'))
            temp_file_path = temp_file.name
            os.chmod(temp_file_path, 0o600)  # Add secure file permissions
            
        csv_filename = f"{uuid.uuid4()}.csv"
        with open(temp_file_path, 'rb') as f:
            file_storage = FileStorage(
                stream=f,
                filename=csv_filename,
                content_type='text/csv'
            )
            csv_file_path = safe_save_file(file_storage, csv_filename)
            csv_file_name = os.path.basename(csv_file_path)
        
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

        # Sanitize data to prevent formula injection
        for col in excel_df.select_dtypes(include=['object']):
            excel_df[col] = excel_df[col].apply(sanitize_for_spreadsheet)
        
        # Save using openpyxl
        excel_df.to_excel(excel_file.name, index=False, engine='openpyxl')
        
        excel_filename = f"{uuid.uuid4()}.xlsx"
        with open(excel_file.name, 'rb') as f:
            file_storage = FileStorage(
                stream=f,
                filename=excel_filename,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            excel_file_path = safe_save_file(file_storage, excel_filename)
            excel_file_name = os.path.basename(excel_file_path)
            
        # Clean up temp file
        if os.path.exists(excel_file.name):
            os.remove(excel_file.name)
            
        # Save URLs securely
        urls = df['video_url'].dropna().tolist()
        url_content = '\n'.join([url for url in urls if url and url.strip()])
        
        url_filename = f"{uuid.uuid4()}.txt"
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(url_content.encode('utf-8'))
            temp_file_path = temp_file.name
            
        with open(temp_file_path, 'rb') as f:
            file_storage = FileStorage(
                stream=f,
                filename=url_filename,
                content_type='text/plain'
            )
            url_file_path = safe_save_file(file_storage, url_filename)
            url_file_name = os.path.basename(url_file_path)
            
        # Clean up temp file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        # Generate structured preview data for template (XSS-safe)
        preview_data = {
            'columns': df.columns.tolist(),
            'rows': df.head(5).values.tolist()
        }

        # Return all necessary data
        return df, csv_file_name, excel_file_name, url_file_name, insights, day_heatmap_name, time_heatmap_name, month_heatmap_name, not df.empty, preview_data

    except ValueError as e:
        # Forward ValueError with its message
        from app.utils.logging_config import log_error_safely
        log_error_safely(e, "TikTok processing ValueError", logger)
        raise ValueError(str(e))
    except Exception as e:
        # Import secure logging functions
        from app.utils.logging_config import log_error_safely, log_stack_trace_safely
        
        log_error_safely(e, "TikTok file processing", logger)
        log_stack_trace_safely(e, logger)
        raise ValueError(f"Error processing TikTok data: {str(e)}")
