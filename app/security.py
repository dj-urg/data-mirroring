from flask import session, redirect, url_for, request, current_app, make_response
from functools import wraps
import os
import glob
import tempfile

def enforce_https():
    """Redirects HTTP to HTTPS only in production."""
    is_production = os.getenv("FLASK_ENV") == "production" or os.getenv("DYNO")  # DYNO is set on Heroku
    if is_production and request.headers.get("X-Forwarded-Proto", "http") == "http":
        response = make_response(redirect(request.url.replace("http://", "https://"), code=301))
        return apply_security_headers(response)  # Apply security headers even on redirects

def apply_security_headers(response):
    """Adds essential security headers to every response."""
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.plot.ly; "
        "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
        "img-src 'self' https://img.icons8.com data:; "
        "font-src 'self' data: https://cdnjs.cloudflare.com; "
        "object-src 'none'; "
        "frame-ancestors 'none';"
    )
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation 'self'; microphone 'none'"
    response.headers["X-XSS-Protection"] = "1; mode=block"

    return response

def requires_authentication(f):
    """Decorator that ensures users are authenticated before accessing routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('routes.enter_code'))
        return f(*args, **kwargs)
    
    return decorated_function

def cleanup_old_temp_files():
    """Deletes CSV files older than 1 hour in the temp directory."""
    temp_dir = tempfile.gettempdir()
    for file in glob.glob(os.path.join(temp_dir, "*.csv")):
        try:
            os.remove(file)
        except Exception:
            pass

def register_cleanup(app):
    """Attach cleanup function to Flask app startup and request teardown."""
    with app.app_context():
        cleanup_old_temp_files()

    @app.teardown_request
    def cleanup_temp_files(exception=None):
        """Delete only files that were marked for deletion."""
        temp_dir = tempfile.gettempdir()

        for filename in getattr(request, "files_to_cleanup", []):
            file_path = os.path.join(temp_dir, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass