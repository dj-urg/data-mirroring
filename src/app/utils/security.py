from flask import session, redirect, url_for, request, current_app, make_response, g
from functools import wraps
import os
import base64
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
    nonce = g.csp_nonce

    # Content-Security-Policy
    response.headers["Content-Security-Policy"] = (
        f"default-src 'none'; "  # Deny all by default
        f"script-src 'self' 'nonce-{nonce}' https://cdnjs.cloudflare.com; "  # Allow scripts with nonce and from trusted CDN
        f"style-src 'self' 'nonce-{nonce}' https://cdnjs.cloudflare.com https://fonts.googleapis.com; " 
        f"style-src-elem 'self' 'nonce-{nonce}' https://cdnjs.cloudflare.com https://data-mirror.org https://data-mirror-72f6ffc87917.herokuapp.com; "  # Add nonce here too!
        f"img-src 'self' https://img.icons8.com https://upload.wikimedia.org data:; "  # Allow trusted image sources
        f"font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com; "  # Allow trusted font sources
        f"object-src 'none'; "  # Disallow plugins like Flash or Java applets
        f"frame-ancestors 'none'; "  # Prevent embedding your site in an iframe
        f"base-uri 'self'; "  # Restrict the base URI to your site only
        f"form-action 'self'; "  # Restrict forms to submit only to your own domain
        f"connect-src 'self' https://data-mirror.org https://data-mirror-72f6ffc87917.herokuapp.com https://cdnjs.cloudflare.com;"  # Allow connections to both domains and CDN
    )

    # Rest of your headers remain the same
    # ...

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
