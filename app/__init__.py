from flask import Flask, request
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
import os
import tempfile
import logging
from dotenv import load_dotenv
from app.extensions import limiter
from app.logging_config import setup_logging
from app.security import enforce_https  # Import the HTTPS enforcement function

load_dotenv()
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__, template_folder="../templates")
    app.secret_key = os.getenv('SECRET_KEY')

    # Load Configurations
    from app.config import configure_app
    configure_app(app)

    # Set up logging AFTER the app is created
    setup_logging(app)

    # Enforce HTTPS before every request (only in production)
    @app.before_request
    def force_https():
        https_redirect = enforce_https()
        if https_redirect:
            return https_redirect

    # Enable CSRF Protection
    csrf = CSRFProtect(app)
    csrf.init_app(app)

    # Enable CORS
    allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS", "https://data-mirror-72f6ffc87917.herokuapp.com").split(",")
    CORS(app, resources={r"/*": {"origins": allowed_origins}})

    # Rate Limiting
    limiter.init_app(app)

    # Register Blueprints (Routes)
    from app.routes import routes_bp
    app.register_blueprint(routes_bp, url_prefix="/")

    @app.teardown_request
    def cleanup_temp_files(exception=None):
        """Delete only files that were marked for deletion."""
        temp_dir = tempfile.gettempdir()

        # Only delete files that were marked in this session
        files_deleted = 0
        for filename in getattr(request, "files_to_cleanup", []):
            file_path = os.path.join(temp_dir, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    files_deleted += 1
                    logger.info(f"Deleted temporary file: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to delete file {file_path}: {e}")

        if files_deleted == 0:
            logger.info("No temporary files to delete.")

    return app