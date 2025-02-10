from flask import Flask, request, g
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
import os
import logging
import secrets
import base64
from dotenv import load_dotenv
from app.extensions import limiter
from app.logging_config import setup_logging
from app.security import enforce_https, apply_security_headers, register_cleanup

load_dotenv()
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__, template_folder="../templates")
    app.secret_key = os.getenv('SECRET_KEY')

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

    # Load configurations
    from app.config import configure_app
    configure_app(app)

    # Set up logging AFTER the app is created
    setup_logging(app)

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

    # Register cleanup functions
    register_cleanup(app)

    return app