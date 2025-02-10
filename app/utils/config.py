import os
from datetime import timedelta

def configure_app(app):
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    app.logger.info("Starting app configuration for environment: %s", FLASK_ENV)

    if FLASK_ENV == 'production':
        app.config.update(
            SESSION_COOKIE_SECURE=True,
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_SAMESITE='Strict',
            SESSION_PERMANENT=False,
            PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
            WTF_CSRF_CHECK_REFERRER=True,
            WTF_CSRF_SSL_STRICT=True,
            MAX_CONTENT_LENGTH=16 * 1024 * 1024,
        )
        app.logger.info(
            "Production configuration applied: "
            "Secure session cookies, CSRF strict enabled, session lifetime of 30 minutes, "
            "and a maximum content length of 16MB."
        )
    else:
        app.config.update(
            SESSION_COOKIE_SECURE=False,
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_SAMESITE='Lax',
        )
        app.logger.info(
            "Development configuration applied: "
            "Non-secure session cookies for easier testing."
        )

    app.logger.info("App configuration completed.")