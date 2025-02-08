from flask import session, redirect, url_for, request, current_app, make_response, g
from functools import wraps
import os
import glob
import tempfile
import time
import secrets
from urllib.parse import urlparse, urlunparse

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

def apply_security_headers(response):
    """Adds essential security headers to every response, ensuring security best practices are applied."""

    # Generate a CSP nonce dynamically per request
    nonce = g.get("csp_nonce", secrets.token_urlsafe(16))

    response.headers["Content-Security-Policy"] = (
        f"default-src 'self'; "
        f"style-src 'self' 'nonce-{nonce}' https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        f"img-src 'self' https://img.icons8.com https://upload.wikimedia.org data:; "
        f"font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
        f"object-src 'none'; "
        f"frame-ancestors 'none'; "
        f"base-uri 'self';"
    )

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(self), microphone=()"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

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
    temp_dir = tempfile.gettempdir()
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
    temp_dir = tempfile.gettempdir()

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
