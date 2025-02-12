from flask import session, redirect, url_for, request, current_app, make_response, g
from functools import wraps
import os
import base64
import time
import secrets
from urllib.parse import urlparse, urlunparse
from app.utils.file_utils import get_user_temp_dir

def enforce_https():
    """Redirects HTTP to HTTPS only in production."""
    is_production = os.getenv("FLASK_ENV") == "production" or os.getenv("DYNO")  # Heroku check

    # Allowed domains for secure redirection
    ALLOWED_HOSTS = {"data-mirror.org", "data-mirror-72f6ffc87917.herokuapp.com"}

    if is_production and request.headers.get("X-Forwarded-Proto", "http") == "http":
        parsed_url = urlparse(request.url)

        # Ensure the hostname is in the allowed list
        if parsed_url.hostname in ALLOWED_HOSTS:
            secure_url = urlunparse(parsed_url._replace(scheme="https"))
            response = make_response(redirect(secure_url, code=301))
            return apply_security_headers(response)

        # Block redirects to untrusted domains
        return "Invalid redirect", 400

import base64
import secrets
from flask import g, request

def apply_security_headers(response):
    """Adds essential security headers to every response, ensuring security best practices are applied."""

    # Generate a CSP nonce dynamically per request
    nonce = g.csp_nonce = base64.b64encode(secrets.token_bytes(16)).decode('utf-8')

    # Content-Security-Policy
    response.headers["Content-Security-Policy"] = (
        f"default-src 'none'; "  # Deny all by default
        f"script-src 'self' 'nonce-{nonce}' https://cdnjs.cloudflare.com; "  # Allow scripts with nonce and from trusted CDN
        f"style-src 'self' https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        f"style-src-elem 'self' https://data-mirror.org https://data-mirror-72f6ffc87917.herokuapp.com; "# Allow styles from your app and trusted CDNs
        f"img-src 'self' https://img.icons8.com https://upload.wikimedia.org data:; "  # Allow trusted image sources
        f"font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com; "  # Allow trusted font sources
        f"object-src 'none'; "  # Disallow plugins like Flash or Java applets
        f"frame-ancestors 'none'; "  # Prevent embedding your site in an iframe
        f"base-uri 'self'; "  # Restrict the base URI to your site only
        f"form-action 'self'; "  # Restrict forms to submit only to your own domain
        f"connect-src 'self' https://data-mirror.org https://data-mirror-72f6ffc87917.herokuapp.com;"  # Allow connections to both domains
    )

    # X-Content-Type-Options
    response.headers["X-Content-Type-Options"] = "nosniff"

    # X-Frame-Options
    response.headers["X-Frame-Options"] = "DENY"

    # Strict-Transport-Security
    if request.is_secure:  # Apply HSTS only for HTTPS
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

    # Referrer-Policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Permissions-Policy
    response.headers["Permissions-Policy"] = "geolocation=(self), microphone=()"

    # Cross-Origin-Opener-Policy
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"

    # Cross-Origin-Resource-Policy
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

    # Add CORS Header to Allow Specific Origins
    allowed_origins = ["https://data-mirror.org", "https://data-mirror-72f6ffc87917.herokuapp.com"]
    origin = request.headers.get("Origin")
    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"  # Required for dynamic Access-Control-Allow-Origin

    return response

def requires_authentication(f):
    """Decorator that ensures users are authenticated before accessing routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('routes.enter_code'))
        return f(*args, **kwargs)
    
    return decorated_function
                
def cleanup_old_temp_files(exception=None):
    """Deletes temporary files older than 1 hour in the temp directory."""
    temp_dir = get_user_temp_dir()
    one_hour_ago = time.time() - 3600  # 1 hour ago

    try:
        for file in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, file)

            # Ensure it's a file (not a directory) and is older than 1 hour
            if os.path.isfile(file_path) and os.path.getmtime(file_path) < one_hour_ago:
                os.remove(file_path)
                current_app.logger.info(f"Deleted old temp file: {file_path}")
    except Exception as e:
        current_app.logger.error(f"Error during temp file cleanup: {e}")

def cleanup_temp_files(exception=None):
    """Deletes only files that were marked for deletion in the request context."""
    temp_dir = get_user_temp_dir()

    if hasattr(g, "files_to_cleanup"):
        for filename in g.files_to_cleanup:
            file_path = os.path.join(temp_dir, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    current_app.logger.info(f"Deleted temporary file: {file_path}")
                except Exception as e:
                    current_app.logger.error(f"Failed to delete file {file_path}: {e}")

def register_cleanup(app):
    """Registers cleanup functions with Flask request lifecycle."""
    
    @app.before_request
    def initialize_request_cleanup():
        """Ensure request.files_to_cleanup exists before each request."""
        g.files_to_cleanup = []

    @app.teardown_request
    def cleanup_temp_files_request(exception=None):
        """Delete only files that were marked for deletion in the request context, and old temp files."""
        cleanup_temp_files(exception)        # Cleanup files marked for deletion
        cleanup_old_temp_files(exception)    # Cleanup old temp files (older than 1 hour)

    app.logger.info("Cleanup functions registered.")
