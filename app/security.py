from flask import session, redirect, url_for, request, current_app
from functools import wraps
import os
import glob
import tempfile

def apply_security_headers(response):
    """
    Adds security headers to every response and logs their application.
    """
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
    response.headers["Feature-Policy"] = "geolocation 'self'; microphone 'none'"
    response.headers["X-XSS-Protection"] = "1; mode=block"

    #Log that security headers were applied
    current_app.logger.info("Security headers applied to response.")

    return response

def requires_authentication(f):
    """
    Decorator that ensures users are authenticated before accessing routes.
    Logs authentication attempts.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            current_app.logger.warning(f"Unauthorized access attempt: {request.path} from {request.remote_addr}")
            return redirect(url_for('routes.enter_code'))
        
        current_app.logger.debug(f"Authenticated access: {request.path} from {request.remote_addr}")
        return f(*args, **kwargs)

    return decorated_function

def cleanup_old_temp_files():
    """Deletes CSV files older than 1 hour in the temp directory."""
    temp_dir = tempfile.gettempdir()
    current_app.logger.info(f"Checking temp directory for old files: {temp_dir}")

    for file in glob.glob(os.path.join(temp_dir, "*.csv")):
        try:
            os.remove(file)
            current_app.logger.info(f"Deleted old temp file: {file}")
        except Exception as e:
            current_app.logger.error(f"Could not delete {file}: {e}")

def register_cleanup(app):
    """Attach cleanup to Flask startup."""
    with app.app_context():
        cleanup_old_temp_files()
