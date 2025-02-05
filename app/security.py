from flask import session, redirect, url_for, request, current_app, make_response, g
from functools import wraps
import os
import glob
import tempfile
import secrets

def enforce_https():
    """Redirects HTTP to HTTPS only in production."""
    is_production = os.getenv("FLASK_ENV") == "production" or os.getenv("DYNO")  # DYNO is set on Heroku
    if is_production and request.headers.get("X-Forwarded-Proto", "http") == "http":
        response = make_response(redirect(request.url.replace("http://", "https://"), code=301))
        return apply_security_headers(response)  # Apply security headers even on redirects

def apply_security_headers(response):
    """Adds essential security headers to every response, ensuring security best practices are applied."""
    
    nonce = g.get("csp_nonce", "")
    
    response.headers["Content-Security-Policy"] = (
        f"default-src 'self'; "
        f"script-src 'self' 'nonce-{nonce}' https://cdn.plot.ly; "
        f"style-src 'self' 'nonce-{nonce}' https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        f"style-src-elem 'self' 'nonce-{nonce}' https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        f"img-src 'self' https://img.icons8.com https://upload.wikimedia.org data:; "
        f"font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
        f"object-src 'none'; "
        f"frame-ancestors 'none';"
    )

    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation 'self'; microphone 'none'"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

    # Store nonce in a secure cookie so it can be used in templates
    response.set_cookie("csp_nonce", nonce, secure=True, httponly=True, samesite="Strict")

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