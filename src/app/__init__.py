from flask import Flask, g
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
import os
import logging
import secrets
import base64
from dotenv import load_dotenv
from flask_limiter.util import get_remote_address
from app.utils.extensions import limiter
from app.utils.logging_config import setup_logging
from app.utils.security import enforce_https, apply_security_headers
from app.utils.file_manager import TemporaryFileManager

load_dotenv()
logger = logging.getLogger(__name__)

def create_app(config_name=None):
    # Dynamically locate the templates folder
    current_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(current_dir, "templates")
    app = Flask(__name__, template_folder=templates_dir)
    
    # Set secret key from environment variables
    secret_key = os.getenv('SECRET_KEY')
    if not secret_key:
        raise ValueError("SECRET_KEY is not set. Please set it in your .env file.")
    app.secret_key = secret_key

    @app.before_request
    def generate_nonce():
        """Generate a Base64-compliant nonce for CSP before rendering templates."""
        g.csp_nonce = base64.b64encode(secrets.token_bytes(16)).decode('utf-8')

    @app.before_request
    def enforce_https_request():
        """Ensure all requests are served over HTTPS in production."""
        return enforce_https()

    @app.after_request
    def apply_headers(response):
        """Apply strict security headers to all responses."""
        return apply_security_headers(response)
        
    @app.context_processor
    def inject_csp_nonce():
        """Make CSP nonce available in templates."""
        return dict(csp_nonce=lambda: getattr(g, 'csp_nonce', ''))

    # Load configurations
    from app.utils.config import configure_app
    configure_app(app)

    # Set up logging AFTER the app is created
    setup_logging(app)

    # Enable CSRF Protection
    csrf = CSRFProtect(app)
    csrf.init_app(app)

    # Enable CORS
    allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS", "https://data-mirror-72f6ffc87917.herokuapp.com").split(",")
    CORS(app, resources={r"/*": {"origins": allowed_origins}})

    # Configure limiter dynamically based on environment
    if os.environ.get('DYNO'):  # Running on Heroku
        storage_string = "memory"
    else:  # Local/dev environment
        rate_limit_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'rate_limits')
        os.makedirs(rate_limit_dir, exist_ok=True)
        os.chmod(rate_limit_dir, 0o700)
        storage_string = f"filesystem:{rate_limit_dir}"
    
    # Initialize limiter with storage_uri parameter
    limiter.init_app(
        app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri=storage_string
    )

    # Register Blueprints (Routes)
    from app.routes import routes_bp
    app.register_blueprint(routes_bp, url_prefix="/")

    # Register cleanup functions
    TemporaryFileManager.register_cleanup(app)

    return app
