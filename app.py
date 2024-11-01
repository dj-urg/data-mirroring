from flask import Flask, render_template, request, send_file, redirect, session, url_for, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from functools import wraps
from datetime import timedelta
import os
import logging
import signal
import sys
import atexit
import tempfile
from dotenv import load_dotenv
from platforms.youtube import process_youtube_file
from platforms.instagram import process_instagram_file
from platforms.tiktok import process_tiktok_file

load_dotenv()

# Initialize Flask app
app = Flask(__name__)

app.secret_key = os.getenv('SECRET_KEY')  # Set the secret key for session management

csrf = CSRFProtect(app)  # Initialize CSRF protection

# Enable Cross-Origin Resource Sharing (CORS) for specific origins
CORS(app, resources={r"/*": {"origins": ["https://data-mirror-72f6ffc87917.herokuapp.com", "https://cdnjs.cloudflare.com"]}})

# Get environment setting (default to 'production')
FLASK_ENV = os.getenv('FLASK_ENV', 'development')

# Route to serve the favicon    
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico')    

# Set session cookie configurations based on environment
if FLASK_ENV == 'production':
    app.config['SESSION_COOKIE_SECURE'] = True  # Only transmit cookies over HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True # Prevent access to session cookies via JavaScript
    app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'  # Prevent CSRF attacks
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # Limit file upload size to 16 MB
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # Set session timeout to 30 minutes
    app.config['WTF_CSRF_CHECK_REFERRER'] = False  # Disable CSRF check for referrer
    app.config['WTF_CSRF_SSL_STRICT'] = False
else:
    # Development mode: No need for HTTPS
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True

if FLASK_ENV == 'production':
    # Disable logging in production except for warnings and errors
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(levelname)s: %(message)s')
else:
    # Enable detailed logging for development
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

logger = logging.getLogger()

# Define the base directory for file storage
BASE_DIR = os.getenv('APP_BASE_DIR', os.path.dirname(os.path.abspath(__file__)))

# Initialize rate limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]  # Adjust based on your needs
)

@app.after_request
def apply_security_headers(response):
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.plot.ly; "  # Allow unsafe-eval for Plotly
        "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "  # Allow Font Awesome and inline styles
        "img-src 'self' https://img.icons8.com data:; "  # Allow images from your domain and icons8
        "font-src 'self' data: https://cdnjs.cloudflare.com; "  # Allow Font Awesome fonts
        "object-src 'none'; "  # Disallow object embedding
        "frame-ancestors 'none'; "  # Prevent your site from being embedded in iframes
    )
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Feature-Policy"] = "geolocation 'self'; microphone 'none'"
    response.headers["X-XSS-Protection"] = "1; mode=block"

    return response

# Code entry route
@app.route('/enter-code', methods=['GET', 'POST'])
def enter_code():
    ACCESS_CODE = os.getenv('ACCESS_CODE')
    if request.method == 'POST':
        code = request.form.get('code')
        if code == ACCESS_CODE:
            session['authenticated'] = True  # Set authenticated status in the session
            return redirect(url_for('landing_page'))
        else:
            return render_template('enter_code.html', error="Invalid access code.")
    return render_template('enter_code.html')

# Logout route
@app.route('/logout')
def logout():
    session.clear()  # Clear the session
    return redirect(url_for('enter_code'))  # Redirect to the login page

def requires_authentication(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('enter_code'))  # Redirect to enter code if not authenticated
        return f(*args, **kwargs)
    return decorated_function

# Gracefully shut down the app
def graceful_shutdown(signal, frame):
    if FLASK_ENV != 'production':
        logger.info("Graceful shutdown initiated")
    sys.exit(0)

signal.signal(signal.SIGINT, graceful_shutdown)
signal.signal(signal.SIGTERM, graceful_shutdown)

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
    if FLASK_ENV != 'production':
        # Show detailed error information in development
        return f"Error: {str(e)}", 500
    else:
        # Show a generic error message in production
        logger.error(f"An internal error occurred: {e}")
        return "An internal error occurred. Please try again later.", 500
    
# Landing page route
@app.route('/')
@requires_authentication
def landing_page():
    return render_template('homepage.html')

# Platform selection page route
@app.route('/platform-selection')
@requires_authentication
def platform_selection():
    return render_template('platform_selection.html')

# Information page route
@app.route('/info')
@requires_authentication
def info():
    return render_template('info.html')

# Data processing information page route
@app.route('/data_processing_info')
@requires_authentication
def data_processing_info():
    return render_template('data_processing_info.html')

# Dashboard route that selects platform and handles both GET and POST
@app.route('/dashboard/<platform>', methods=['GET', 'POST'])
@requires_authentication
@limiter.limit("10 per minute")     # Rate limit to 10 requests per minute
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
            df, unique_filename, insights, bump_chart_name, heatmap_name, has_valid_data = process_youtube_file(files)
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
            plot_data=bump_chart_name,  # This is for the bump chart (most watched channels)
            heatmap_data=heatmap_name,  # This is for the heatmap (day of the week consumption)
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
        tmp_file.close()
        return tmp_file.name

# Route to download the processed CSV file
@app.route('/download_csv/<filename>', methods=['GET'])
@limiter.limit("5 per minute")  # Limit to 5 downloads per minute
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

# Helper function to save a Matplotlib plot as a temporary image file
def save_image_temp_file(fig):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
        fig.savefig(tmp_file.name, bbox_inches='tight')
        tmp_file.close()
        return tmp_file.name

# Route to download the generated image
@app.route('/download_image/<filename>', methods=['GET'])
@limiter.limit("5 per minute")  # Limit to 5 downloads per minute
def download_image(filename):
    # Construct the full path to the temporary file
    temp_file_path = os.path.join(tempfile.gettempdir(), filename)

    # Check if the file exists
    if os.path.exists(temp_file_path):
        # Log the download action
        logger.info(f"Image file downloaded: {temp_file_path}")

        # Serve the image and delete it afterward
        response = send_file(temp_file_path, mimetype='image/png')
        os.remove(temp_file_path)  # Delete the file after sending
        return response

    return "File not found", 404
    
# Teardown request function for cleaning up files
@app.teardown_request
def cleanup_temp_files(exception=None):
    # Clean up the temporary files after the request finishes
    temp_file_path = session.get('csv_file', None)
    if temp_file_path and os.path.exists(temp_file_path):
        try:
            os.remove(temp_file_path)
        except Exception as e:
            logger.error(f"Failed to delete temp file: {e}")
        finally:
            session.pop('csv_file', None)  # Ensure session is cleaned up

    # Similarly, for image cleanup
    image_file_path = session.get('image_file', None)
    if image_file_path and os.path.exists(image_file_path):
        try:
            os.remove(image_file_path)
        except Exception as e:
            logger.error(f"Failed to delete temp image file: {e}")
        finally:
            session.pop('image_file', None)

# Define the port to run the app on
PORT = int(os.getenv('PORT', 5001))  # Default to 5001 for local development

# Run the Flask app
if __name__ == '__main__':
    logger.info(f'Starting Flask app on port {PORT}')
    app.run(port=PORT, host='0.0.0.0', debug=True, threaded=True)