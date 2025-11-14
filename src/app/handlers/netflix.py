import json
import pandas as pd
import os
import tempfile
import uuid
import logging
import matplotlib
import matplotlib.pyplot as plt
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

def save_image_temp_file(fig):
    """Saves an image in the user's temporary directory and returns the filename."""
    temp_dir = get_user_temp_dir()  # Get session-specific temp directory
    unique_filename = f"{uuid.uuid4()}.png"  # Generate a unique filename
    temp_file_path = os.path.join(temp_dir, unique_filename)

    # Increase DPI for higher quality while maintaining figure dimensions
    fig.savefig(temp_file_path, 
                bbox_inches='tight',
                dpi=100,              # Higher DPI for better quality
                format='png',         # Explicitly use PNG format
                transparent=False,    # Ensure non-transparent background
                pad_inches=0.1)       # Small padding to avoid clipping
    
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

def generate_heatmap(day_counts):
    """Generates a heatmap showing Netflix viewing by day of the week with no grid lines."""
    # Convert day counts to a dataframe
    day_count_df = pd.DataFrame({'Day': day_counts.index, 'Count': day_counts.values}).set_index('Day')
    
    # Create a heatmap
    fig, ax = plt.subplots(figsize=(8, 2))  # Adjust size for heatmap
    
    # Create heatmap with all grid lines removed
    sns.heatmap(
        day_count_df.T, 
        annot=True, 
        fmt=".0f", 
        cmap="Reds",  # Use red color scheme for Netflix
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

def generate_month_heatmap(df):
    """Generates a heatmap showing Netflix viewing by month with absolutely no grid lines."""
    # Extract month and year from timestamp
    df['month'] = pd.to_datetime(df['timestamp']).dt.month
    df['year'] = pd.to_datetime(df['timestamp']).dt.year
    
    # Create a pivot table to count views by month and year
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
        fmt=".0f",           # Format as integers (handles floats)
        cmap="Reds",         # Red color map for Netflix
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
    """Generates a heatmap showing Netflix viewing by time of day with no grid lines."""
    # Extract hour from timestamp
    df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
    
    # Count views by hour
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
        fmt=".0f", 
        cmap="Reds",  # Red color scheme for Netflix
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

def generate_genre_treemap(df):
    """Generates a treemap of top genres based on viewing count."""
    # Filter for non-unknown genres
    genres_df = df[df['genre'] != 'Unknown']
    
    if genres_df.empty:
        # Fallback to titles if no genre data
        title_data = df.groupby('title').size().reset_index(name='count')
        title_data.columns = ['genre', 'count']  # Rename for consistency
    else:
        # Group by genre and count views
        title_data = genres_df.groupby('genre').size().reset_index(name='count')
    
    # Sort by view count and get top 15 genres
    title_data = title_data.sort_values('count', ascending=False).head(15)
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Calculate normalized sizes based on counts
    sizes = title_data['count'].values
    labels = [f"{genre}\n({count})" if len(genre) < 15 else f"{genre[:12]}...\n({count})" 
              for genre, count in zip(title_data['genre'], title_data['count'])]
    
    # Create color map
    cmap = plt.get_cmap('Reds')  # Red color scheme for Netflix
    norm = plt.Normalize(min(sizes), max(sizes))
    colors = [cmap(norm(size)) for size in sizes]
    
    # Create the treemap
    import squarify
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

# Main data processing function
def process_netflix_file(files):
    """Processes multiple Netflix CSV data files and returns insights and plot data."""
    try:
        all_data = []

        for file in files:
            try:
                # Read CSV file
                df = pd.read_csv(file)
                logger.info(f"Processing Netflix CSV file: {file.filename}")
                logger.info(f"Columns found: {list(df.columns)}")
                
                # Process IndicatedPreferences.csv
                if 'Profile Name' in df.columns and 'Show' in df.columns:
                    logger.info("Processing IndicatedPreferences data")
                    for _, row in df.iterrows():
                        # Extract and validate event date
                        event_date = row.get('Event Date', '')
                        timestamp = pd.to_datetime(event_date, errors='coerce')
                        
                        # Skip items with invalid timestamps
                        if pd.isnull(timestamp):
                            logger.warning(f"Skipping Netflix item with invalid timestamp: {event_date}")
                            continue
                        
                        # Extract data with validation
                        profile_name = str(row.get('Profile Name', 'Unknown'))
                        show_title = str(row.get('Show', 'No Title'))
                        has_watched = row.get('Has Watched', '')
                        is_interested = row.get('Is Interested', '')
                        
                        all_data.append({
                            'title': show_title,
                            'timestamp': timestamp,
                            'profile_name': profile_name,
                            'has_watched': has_watched,
                            'is_interested': is_interested,
                            'content_type': 'Preference',
                            'genre': 'Unknown',
                            'country': 'Unknown'
                        })
                
                # Process MyList.csv
                elif 'Profile Name' in df.columns and 'Title Name' in df.columns and 'Country' in df.columns:
                    logger.info("Processing MyList data")
                    for _, row in df.iterrows():
                        # Extract and validate add date
                        add_date = row.get('Utc Title Add Date', '')
                        timestamp = pd.to_datetime(add_date, errors='coerce')
                        
                        # Skip items with invalid timestamps
                        if pd.isnull(timestamp):
                            logger.warning(f"Skipping Netflix item with invalid timestamp: {add_date}")
                            continue
                        
                        # Extract data with validation
                        profile_name = str(row.get('Profile Name', 'Unknown'))
                        title_name = str(row.get('Title Name', 'No Title'))
                        country = str(row.get('Country', 'Unknown'))
                        
                        all_data.append({
                            'title': title_name,
                            'timestamp': timestamp,
                            'profile_name': profile_name,
                            'content_type': 'MyList',
                            'country': country,
                            'has_watched': '',
                            'is_interested': '',
                            'genre': 'Unknown'
                        })
                
                # Process Ratings.csv
                elif 'Profile Name' in df.columns and 'Title Name' in df.columns and 'Rating Type' in df.columns:
                    logger.info("Processing Ratings data")
                    for _, row in df.iterrows():
                        # Extract and validate event timestamp
                        event_ts = row.get('Event Utc Ts', '')
                        timestamp = pd.to_datetime(event_ts, errors='coerce')
                        
                        # Skip items with invalid timestamps
                        if pd.isnull(timestamp):
                            logger.warning(f"Skipping Netflix item with invalid timestamp: {event_ts}")
                            continue
                        
                        # Extract data with validation
                        profile_name = str(row.get('Profile Name', 'Unknown'))
                        title_name = str(row.get('Title Name', 'No Title'))
                        rating_type = str(row.get('Rating Type', 'Unknown'))
                        star_value = row.get('Star Value', '')
                        thumbs_value = row.get('Thumbs Value', '')
                        device_model = str(row.get('Device Model', 'Unknown'))
                        region_view_date = row.get('Region View Date', '')
                        
                        all_data.append({
                            'title': title_name,
                            'timestamp': timestamp,
                            'profile_name': profile_name,
                            'content_type': 'Rating',
                            'rating_type': rating_type,
                            'star_value': star_value,
                            'thumbs_value': thumbs_value,
                            'device_model': device_model,
                            'region_view_date': region_view_date,
                            'country': 'Unknown',
                            'has_watched': '',
                            'is_interested': '',
                            'genre': 'Unknown'
                        })
                
                # Process SearchHistory.csv
                elif 'Profile Name' in df.columns and 'Query Typed' in df.columns and 'Utc Timestamp' in df.columns:
                    logger.info("Processing SearchHistory data")
                    for _, row in df.iterrows():
                        # Extract and validate timestamp
                        utc_timestamp = row.get('Utc Timestamp', '')
                        timestamp = pd.to_datetime(utc_timestamp, errors='coerce')
                        
                        # Skip items with invalid timestamps
                        if pd.isnull(timestamp):
                            logger.warning(f"Skipping Netflix item with invalid timestamp: {utc_timestamp}")
                            continue
                        
                        # Extract data with validation
                        profile_name = str(row.get('Profile Name', 'Unknown'))
                        country_iso = str(row.get('Country Iso Code', 'Unknown'))
                        device = str(row.get('Device', 'Unknown'))
                        is_kids = row.get('Is Kids', 0)
                        query_typed = str(row.get('Query Typed', ''))
                        displayed_name = str(row.get('Displayed Name', ''))
                        action = str(row.get('Action', 'Unknown'))
                        section = str(row.get('Section', 'Unknown'))
                        
                        all_data.append({
                            'title': displayed_name if displayed_name else query_typed,
                            'timestamp': timestamp,
                            'profile_name': profile_name,
                            'content_type': 'Search',
                            'country': country_iso,
                            'device_model': device,
                            'is_kids': is_kids,
                            'query_typed': query_typed,
                            'displayed_name': displayed_name,
                            'action': action,
                            'section': section,
                            'has_watched': '',
                            'is_interested': '',
                            'genre': 'Unknown'
                        })
                
                # Process ViewingActivity.csv
                elif 'Profile Name' in df.columns and 'Start Time' in df.columns and 'Title' in df.columns:
                    logger.info("Processing ViewingActivity data")
                    for _, row in df.iterrows():
                        # Extract and validate start time
                        start_time = row.get('Start Time', '')
                        timestamp = pd.to_datetime(start_time, errors='coerce')
                        
                        # Skip items with invalid timestamps
                        if pd.isnull(timestamp):
                            logger.warning(f"Skipping Netflix item with invalid timestamp: {start_time}")
                            continue
                        
                        # Extract data with validation
                        profile_name = str(row.get('Profile Name', 'Unknown'))
                        title = str(row.get('Title', 'No Title'))
                        duration = str(row.get('Duration', '00:00:00'))
                        attributes = str(row.get('Attributes', ''))
                        supplemental_video_type = str(row.get('Supplemental Video Type', ''))
                        device_type = str(row.get('Device Type', 'Unknown'))
                        bookmark = str(row.get('Bookmark', '00:00:00'))
                        latest_bookmark = str(row.get('Latest Bookmark', '00:00:00'))
                        country = str(row.get('Country', 'Unknown'))
                        
                        # Extract country code from country field (e.g., "BE (Belgium)" -> "BE")
                        country_code = country.split(' ')[0] if ' ' in country else country
                        
                        all_data.append({
                            'title': title,
                            'timestamp': timestamp,
                            'profile_name': profile_name,
                            'content_type': 'Viewing',
                            'country': country_code,
                            'device_model': device_type,
                            'duration': duration,
                            'attributes': attributes,
                            'supplemental_video_type': supplemental_video_type,
                            'bookmark': bookmark,
                            'latest_bookmark': latest_bookmark,
                            'has_watched': 'Yes',
                            'is_interested': '',
                            'genre': 'Unknown'
                        })
                
                # Add other CSV file types here as needed
                else:
                    logger.warning(f"Unknown CSV format in file: {file.filename}")
                    continue
                
            except Exception as e:
                logger.warning(f"Error processing Netflix CSV file: {str(e)}")
                continue

        # Check if we have valid data
        if not all_data:
            logger.warning("No valid data found in uploaded Netflix files")
            raise ValueError("No valid data found in the uploaded files. Please check the file format.")

        df = pd.DataFrame(all_data)
        
        # Generate insights
        insights = {
            'total_items': len(df),
            'time_frame_start': df['timestamp'].min().date() if not df.empty else 'N/A',
            'time_frame_end': df['timestamp'].max().date() if not df.empty else 'N/A',
            'unique_titles': df['title'].nunique(),
            'unique_profiles': df['profile_name'].nunique() if 'profile_name' in df.columns else 0,
            'preferences_count': len(df[df['content_type'] == 'Preference']) if 'content_type' in df.columns else 0,
            'mylist_count': len(df[df['content_type'] == 'MyList']) if 'content_type' in df.columns else 0,
            'ratings_count': len(df[df['content_type'] == 'Rating']) if 'content_type' in df.columns else 0,
            'search_count': len(df[df['content_type'] == 'Search']) if 'content_type' in df.columns else 0,
            'viewing_count': len(df[df['content_type'] == 'Viewing']) if 'content_type' in df.columns else 0,
            'unique_countries': df['country'].nunique() if 'country' in df.columns else 0,
            'unique_devices': df['device_model'].nunique() if 'device_model' in df.columns else 0,
            'thumbs_up_count': len(df[df['thumbs_value'] == 2]) if 'thumbs_value' in df.columns else 0,
            'thumbs_down_count': len(df[df['thumbs_value'] == 1]) if 'thumbs_value' in df.columns else 0,
            'unique_queries': df['query_typed'].nunique() if 'query_typed' in df.columns else 0,
            'kids_searches': len(df[df['is_kids'] == 1]) if 'is_kids' in df.columns else 0,
            'play_actions': len(df[df['action'] == 'play']) if 'action' in df.columns else 0,
            'select_actions': len(df[df['action'] == 'select']) if 'action' in df.columns else 0,
            'trailer_count': len(df[df['supplemental_video_type'] == 'TRAILER']) if 'supplemental_video_type' in df.columns else 0,
            'autoplayed_count': len(df[df['attributes'].str.contains('Autoplayed', na=False)]) if 'attributes' in df.columns else 0,
            'total_watch_time': df['duration'].sum() if 'duration' in df.columns else '00:00:00'
        }

        # Prepare data for visualization
        df['year'] = pd.to_datetime(df['timestamp']).dt.year
        df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.day_name()  # Get day of the week

        # Count the number of views on each day of the week
        day_counts = df['day_of_week'].value_counts().reindex(
            ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        )

        # Generate day of week heatmap image
        day_heatmap_name = save_image_temp_file(generate_heatmap(day_counts))
        
        # Generate month heatmap image
        month_heatmap_name = save_image_temp_file(generate_month_heatmap(df))
        
        # Generate time of day heatmap image
        time_heatmap_name = save_image_temp_file(generate_time_of_day_heatmap(df))

        # Generate genre treemap
        genre_treemap_name = save_image_temp_file(generate_genre_treemap(df))

        # Save CSV data securely
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
        
        # Generate structured preview data for template (XSS-safe)
        preview_data = {
            'columns': df.columns.tolist(),
            'rows': df.head(5).values.tolist()
        }

        return df, excel_filename, unique_filename, insights, genre_treemap_name, day_heatmap_name, month_heatmap_name, time_heatmap_name, not df.empty, preview_data

    except ValueError as e:
        # Forward ValueError with its original message
        logger.warning(f"ValueError in Netflix processing: {str(e)}")
        raise ValueError(str(e))
    except Exception as e:
        logger.warning(f"Error processing Netflix data: {type(e).__name__} - {str(e)}")
        raise ValueError("An internal error occurred. Please try again.")
