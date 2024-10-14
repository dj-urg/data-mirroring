from flask import Flask, render_template, request, send_file, url_for
from flask_talisman import Talisman
from flask_cors import CORS
import os
import logging
import signal
import sys
import atexit
from platforms.youtube import process_youtube_file
from platforms.instagram import process_instagram_file
from platforms.tiktok import process_tiktok_file

app = Flask(__name__)
CORS(app)

# Enable Talisman for HTTPS redirection
Talisman(app, force_https=True)

# Set FLASK_ENV from environment variables, default to 'development'
FLASK_ENV = os.getenv('FLASK_ENV', 'development')

# Configure logging based on environment
if FLASK_ENV == 'production':
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(levelname)s: %(message)s')
else:
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

# Example of logging an error manually
logger = logging.getLogger()

BASE_DIR = os.getenv('APP_BASE_DIR', os.path.dirname(os.path.abspath(__file__)))

# Use a writable directory within your project folder
download_dir = os.path.join(BASE_DIR, 'downloads')  # Change to a writable path
upload_dir = os.path.join(BASE_DIR, 'uploads')  # Change to a writable path

os.makedirs(download_dir, exist_ok=True)
os.makedirs(upload_dir, exist_ok=True)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Set max upload size to 16MB

def graceful_shutdown(signal, frame):
    logger.info("Shutting down gracefully...")
    sys.exit(0)

def cleanup():
    logger.info("Cleaning up before exiting...")

# Register the signal handler for both SIGINT and SIGTERM
signal.signal(signal.SIGINT, graceful_shutdown)
signal.signal(signal.SIGTERM, graceful_shutdown)
# Register cleanup handler for when the script exits
atexit.register(cleanup)

# Allowed extensions
allowed_extensions = {'json'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.before_request
def log_request_info():
    if os.getenv('FLASK_ENV') != 'production':
        logger.info(f"Request: method={request.method}, path={request.path}")

# Log all errors in the app
@app.errorhandler(Exception)
def handle_exception(e):
    # Only log the type of the error, not the data content
    logger.error(f"An error occurred: {type(e).__name__}")
    return "An internal error occurred", 500

# Route for the landing page
@app.route('/')
def landing_page():
    return render_template('homepage.html')

# Route for platform selection
@app.route('/platform-selection')
def platform_selection():
    return render_template('platform_selection.html')

# Route for information about the project
@app.route('/info')
def info():
    return render_template('info.html')

# Route for information about the project
@app.route('/data_processing_info')
def data_processing_info():
    return render_template('data_processing_info.html')

# Route for the dashboard, based on platform selection
@app.route('/dashboard/<platform>', methods=['GET', 'POST'])
def dashboard(platform):
    if request.method == 'GET':
        if platform == 'youtube':
            return render_template('dashboard_youtube.html', plot_data={})
        elif platform == 'instagram':
            return render_template('dashboard_instagram.html', plot_data={})
        elif platform == 'tiktok':
            return render_template('dashboard_tiktok.html')
    
    if request.method == 'POST':
        files = request.files.getlist('file')
        
        if not files or files[0].filename == '':
            return render_template(f'dashboard_{platform}.html', error="No files uploaded.")
        
        # Check if all files are JSON
        for file in files:
            if not allowed_file(file.filename):
                return render_template(f'dashboard_{platform}.html', error="Only JSON files are allowed.")
        
        # Process files based on the platform
        try:
            if platform == 'youtube':
                df, csv_file_path, insights, plot_data, has_valid_data = process_youtube_file(files)
                # Check if plot_data is empty or None
                if not plot_data or not plot_data.get('years'):
                    return render_template('dashboard_youtube.html', error="No valid plot data available.")
            elif platform == 'instagram':
                df, csv_file_path, insights, plot_data, has_valid_data = process_instagram_file(files)
            elif platform == 'tiktok':
                df, csv_file_path, insights, plot_data, has_valid_data = process_tiktok_file(files)
            else:
                return "Invalid platform", 400

            if df.empty:
                return render_template(f'dashboard_{platform}.html', error="No valid data found in the uploaded files.")
            
            first_five_rows = df.head(5).to_html(classes='data', header="true", index=False)
            
            return render_template(
                f'dashboard_{platform}.html',
                insights=insights, 
                csv_file_path=url_for('download_file', filename=os.path.basename(csv_file_path)) if has_valid_data else None,
                data=first_five_rows,
                plot_data=plot_data if plot_data else {},
                uploaded_files=[file.filename for file in files],
                has_valid_data=has_valid_data  # Pass the boolean to the template
            )
        
        except Exception as e:
            logger.error(f"Error processing {platform} data: {e}")
            return render_template(f'dashboard_{platform}.html', error=f"There was an error processing the {platform} data. Please try again.")
    
    return render_template('platform_selection.html')

# Route to download the CSV file
@app.route('/download_file/<filename>')
def download_file(filename):
    file_path = os.path.join(download_dir, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        logger.error(f"File {filename} not found at {file_path}")
        return "File not found", 404

PORT = int(os.getenv('PORT', 5001))
if __name__ == '__main__':
    logger.info(f'Starting Flask app on port {PORT}')
    app.run(port=PORT, host='0.0.0.0', debug=True, threaded=True)