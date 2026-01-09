import os
from datetime import timedelta

def configure_app(app):
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    app.logger.info("Starting app configuration for environment: %s", FLASK_ENV)
    
    if not os.getenv('ACCESS_CODE_HASH'):
        app.logger.error("ACCESS_CODE_HASH is not set in environment variables! App cannot start safely.")
        raise ValueError("ACCESS_CODE_HASH is not set. Authentication will fail.")

    # Default to Safe Security Headers (Lax) to prevent None
    app.config.update(
        SESSION_COOKIE_SAMESITE='Lax',
        REMEMBER_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_HTTPONLY=True,
    )

    if FLASK_ENV == 'production':
        # Normalize TRUSTED_HOSTS (lowercase, strip, strip trailing dot, IDNA)
        raw_hosts = [h for h in os.getenv('TRUSTED_HOSTS', '').split(',') if h.strip()]
        normalized_hosts = []
        for h in raw_hosts:
            hh = h.strip().lower()
            if hh.endswith('.'):
                hh = hh[:-1]
            try:
                hh = hh.encode('idna').decode('ascii')
            except UnicodeError:
                pass
            normalized_hosts.append(hh)

        app.config.update(
            SESSION_COOKIE_SECURE=True,
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_SAMESITE='Strict',
            REMEMBER_COOKIE_SAMESITE='Strict',
            SESSION_PERMANENT=False,
            PERMANENT_SESSION_LIFETIME=timedelta(hours=2),
            WTF_CSRF_CHECK_REFERRER=True,
            WTF_CSRF_SSL_STRICT=True,
            MAX_CONTENT_LENGTH=16 * 1024 * 1024,
            MAX_FORM_MEMORY_SIZE=500 * 1024,  # 500KB
            MAX_FORM_PARTS=1000,
            TRUSTED_HOSTS=normalized_hosts,
        )
        app.logger.info(
            "Production configuration applied: "
            "Secure session cookies, CSRF strict enabled, session lifetime of 2 hours, "
            "max content length 16MB, form limits 500KB/1000 parts, trusted hosts configured."
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