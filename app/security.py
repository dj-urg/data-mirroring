from flask import session, redirect, url_for, request, current_app, make_response, g
from functools import wraps
import os
import glob
import tempfile
import time
import secrets

def enforce_https():
    """Redirects HTTP to HTTPS only in production."""
    is_production = os.getenv("FLASK_ENV") == "production" or os.getenv("DYNO")  # DYNO is set on Heroku
    if is_production and request.headers.get("X-Forwarded-Proto", "http") == "http":
        response = make_response(redirect(request.url.replace("http://", "https://"), code=301))
        return apply_security_headers(response)  # Apply security headers even on redirects
    return None

def apply_security_headers(response):
    """Adds essential security headers to every response, ensuring security best practices are applied."""

    # Generate a CSP nonce dynamically per request
    nonce = g.get("csp_nonce", secrets.token_urlsafe(16))

    response.headers["Content-Security-Policy"] = (
        f"default-src 'self'; "
        f"script-src 'self' 'nonce-{nonce}' https://cdn.plot.ly; "
        f"style-src 'self' 'nonce-{nonce}' https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        f"img-src 'self' https://img.icons8.com https://upload.wikimedia.org data:; "
        f"font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
        f"object-src 'none'; "
        f"frame-ancestors 'none';"
    )

    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(self), microphone=()"
    response.headers["X-XSS-Protection"] = "1; mode=block"
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
    """Deletes CSV files older than 1 hour in the temp directory."""
    temp_dir = tempfile.gettempdir()
    one_hour_ago = time.time() - 3600  # 3600 seconds = 1 hour

    for file in glob.glob(os.path.join(temp_dir, "*.csv")):
        if os.path.getmtime(file) < one_hour_ago:  # Only delete old files
            try:
                os.remove(file)
                current_app.logger.info(f"Deleted old temp file: {file}")
            except Exception as e:
                current_app.logger.error(f"Failed to delete old temp file {file}: {e}")
                
def cleanup_temp_files(exception=None):
    """Delete only files that were marked for deletion in the request context."""
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
        """Delete only files that were marked for deletion in the request context."""
        cleanup_temp_files(exception)

    @app.teardown_request
    def cleanup_old_temp_files_request(exception=None):
        """Deletes old CSV temp files after requests finish."""
        cleanup_old_temp_files(exception)

    app.logger.info("Cleanup functions registered.")