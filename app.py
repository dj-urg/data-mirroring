from flask import Flask, render_template, request, send_file, redirect, session, abort
from flask_cors import CORS
import os
import logging
import signal
import sys
import atexit
import tempfile
from datetime import timedelta
from platforms.youtube import process_youtube_file
from platforms.instagram import process_instagram_file
from platforms.tiktok import process_tiktok_file

# Initialize Flask app
app = Flask(__name__)

# Enable Cross-Origin Resource Sharing (CORS) for specific origins
CORS(app, resources={r"/*": {"origins": ["https://data-mirror-72f6ffc87917.herokuapp.com", "https://cdnjs.cloudflare.com"]}})

# Set session lifetime (e.g., 60 minutes)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)

# Get environment setting (default to 'production')
FLASK_ENV = os.getenv('FLASK_ENV', 'production')

# Set session cookie configurations based on environment
if FLASK_ENV == 'production':
    app.config['SESSION_COOKIE_SECURE'] = True  # Only transmit cookies over HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent access to session cookies via JavaScript
else:
    # Development mode: No need for HTTPS
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Always prevent JavaScript access

# Configure logging based on environment
if FLASK_ENV == 'production':
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(levelname)s: %(message)s')
else:
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

# Create logger
logger = logging.getLogger()

# Define the base directory for file storage
BASE_DIR = os.getenv('APP_BASE_DIR', os.path.dirname(os.path.abspath(__file__)))

# Define upload and download directories
download_dir = os.path.join(BASE_DIR, 'downloads')
upload_dir = os.path.join(BASE_DIR, 'uploads')

# Create the directories if they don't exist
os.makedirs(download_dir, exist_ok=True)
os.makedirs(upload_dir, exist_ok=True)

# Set a secret key for session management
secret_key = os.urandom(24)
app.secret_key = secret_key

# Set the maximum upload size to 16MB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Gracefully shut down the app
def graceful_shutdown(signal, frame):
    if FLASK_ENV != 'production':
        logger.info("Graceful shutdown initiated")
    sys.exit(0)

def cleanup():
    if FLASK_ENV != 'production':
        logger.info("Cleaning up resources before exiting...")

# Register the signal handler for both SIGINT and SIGTERM
signal.signal(signal.SIGINT, graceful_shutdown)
signal.signal(signal.SIGTERM, graceful_shutdown)

# Register cleanup handler when the script exits
atexit.register(cleanup)

# Allowed file extensions for upload
allowed_extensions = {'json'}

# Function to check if the uploaded file is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Enforce HTTPS in production
@app.before_request
def enforce_https():
    if FLASK_ENV == 'production' and request.scheme != "https":
        return redirect(request.url.replace("http://", "https://"))

# Log requests in non-production environments for debugging
@app.before_request
def log_request_info():
    if os.getenv('FLASK_ENV') != 'production':
        logger.info(f"Request: method={request.method}, path={request.path}")

# General error handler to log exceptions
@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"An error occurred: {type(e).__name__}")
    return "An internal error occurred", 500

# Landing page route
@app.route('/')
def landing_page():
    return render_template('homepage.html')

# Platform selection page route
@app.route('/platform-selection')
def platform_selection():
    return render_template('platform_selection.html')

# Information page route
@app.route('/info')
def info():
    return render_template('info.html')

# Data processing information page route
@app.route('/data_processing_info')
def data_processing_info():
    return render_template('data_processing_info.html')

# Dashboard route that selects platform and handles both GET and POST
@app.route('/dashboard/<platform>', methods=['GET', 'POST'])
def dashboard(platform):
    if request.method == 'GET':
        return render_dashboard_template(platform)

    if request.method == 'POST':
        files = request.files.getlist('file')

        if not files or files[0].filename == '':
            return render_template(f'dashboard_{platform}.html', error="No files uploaded.")

        for file in files:
            if not allowed_file(file.filename):
                return render_template(f'dashboard_{platform}.html', error="Only JSON files are allowed.")

        # Delegate platform-specific processing
        return handle_platform_file_processing(platform, files)


# Helper function to render the initial platform dashboard page
def render_dashboard_template(platform):
    if platform == 'youtube':
        return render_template('dashboard_youtube.html', plot_data={})
    elif platform == 'instagram':
        return render_template('dashboard_instagram.html', plot_data={})
    elif platform == 'tiktok':
        return render_template('dashboard_tiktok.html')
    else:
        return render_template('platform_selection.html')


# Helper function to handle platform-specific file processing
def handle_platform_file_processing(platform, files):
    try:
        # Process files based on the selected platform
        if platform == 'youtube':
            df, unique_filename, insights, plot_data, has_valid_data = process_youtube_file(files)
        elif platform == 'instagram':
            df, unique_filename, insights, plot_data, has_valid_data = process_instagram_file(files)
        elif platform == 'tiktok':
            df, unique_filename, insights, plot_data, heatmap_data, has_valid_data = process_tiktok_file(files)
        else:
            return "Invalid platform", 400

        if not has_valid_data:
            return render_template(f'dashboard_{platform}.html', error="No valid data found in the uploaded files.")

        # Create a secure temporary file for CSV
        temp_file_path = save_csv_temp_file(df)
        session['csv_file'] = temp_file_path  # Store the CSV file path in the session

        if FLASK_ENV != 'production':
            logger.info(f"CSV file created at: {temp_file_path}")

        # Display the first five rows of the processed data
        first_five_rows = df.head(5).to_html(classes='data', header="true", index=False)

        # Render the dashboard with the processed data
        return render_template(
            f'dashboard_{platform}.html',
            insights=insights,
            data=first_five_rows,
            plot_data=plot_data if plot_data else {},
            uploaded_files=[file.filename for file in files],
            has_valid_data=has_valid_data,
            csv_file_name=unique_filename  # Pass the unique filename to the template for download
        )

    except Exception as e:
        logger.error(f"Error processing {platform} data: {e}")
        return render_template(f'dashboard_{platform}.html', error=f"There was an error processing the {platform} data. Please try again.")


# Helper function to save DataFrame as a temporary CSV file
def save_csv_temp_file(df):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
        df.to_csv(tmp_file.name, index=False)
        return tmp_file.name

# Route to download the processed CSV file
@app.route('/download_csv/<filename>', methods=['GET'])
def download_csv(filename):
    # Construct the full file path for the temporary file
    temp_file_path = os.path.join(tempfile.gettempdir(), filename)

    # Check if the file exists
    if os.path.exists(temp_file_path):
        # Log the download action
        logger.info(f"File downloaded: {temp_file_path}")

        # Send the file and delete it afterward
        response = send_file(temp_file_path, as_attachment=True, download_name=filename, mimetype='text/csv')
        os.remove(temp_file_path)  # Delete the file after sending
        session.pop('csv_file', None)  # Clean up session
        return response

    return "File not found", 404

# Make the session permanent for its defined lifetime
@app.before_request
def make_session_permanent():
    session.permanent = True

# Define the port to run the app on
PORT = int(os.getenv('PORT', 5001))  # Default to 5001 for local development

# Run the Flask app
if __name__ == '__main__':
    logger.info(f'Starting Flask app on port {PORT}')
    app.run(port=PORT, host='0.0.0.0', debug=True, threaded=True)