import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    """
    Configures logging based on the environment.
    - Development: Logs are stored in `logs/app.log` with `DEBUG` level.
    - Production: Only `WARNING` and above are printed to stdout.
    """

    log_level = logging.DEBUG if os.getenv("FLASK_ENV", "production") == "development" else logging.WARNING

    log_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(module)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Ensure logs directory exists
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # File handler (only in development)
    if log_level == logging.DEBUG:
        file_handler = RotatingFileHandler("logs/app.log", maxBytes=5 * 1024 * 1024, backupCount=3)
        file_handler.setFormatter(log_formatter)
        file_handler.setLevel(log_level)
        app.logger.addHandler(file_handler)

    # Stream handler (always active)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(log_formatter)
    stream_handler.setLevel(log_level)
    app.logger.addHandler(stream_handler)

    app.logger.setLevel(log_level)

    # Suppress overly verbose logs from libraries in production
    if log_level != logging.DEBUG:
        logging.getLogger("werkzeug").setLevel(logging.WARNING)
        logging.getLogger("flask_limiter").setLevel(logging.WARNING)

    app.logger.info("Logging setup complete.")