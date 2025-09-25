import logging
import os
import re
import hashlib
from logging.handlers import RotatingFileHandler
from typing import Any

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
        try:
            os.makedirs("logs", exist_ok=True)  # Add exist_ok=True to prevent error if directory exists
        except Exception as e:
            app.logger.warning(f"Could not create logs directory: {e}")

    # File handler (only in development)
    if log_level == logging.DEBUG:
        try:
            file_handler = RotatingFileHandler("logs/app.log", maxBytes=5 * 1024 * 1024, backupCount=3)
            file_handler.setFormatter(log_formatter)
            file_handler.setLevel(log_level)
            app.logger.addHandler(file_handler)
        except Exception as e:
            app.logger.warning(f"Could not set up file logging: {e}")

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


def sanitize_log_data(data: Any, max_length: int = 100) -> str:
    """
    Sanitize data to remove sensitive information before logging.
    
    Args:
        data: The data to sanitize
        max_length: Maximum length of sanitized string
        
    Returns:
        str: Sanitized data safe for logging
    """
    if data is None:
        return "None"
    
    # Convert to string if not already
    data_str = str(data)
    
    # Truncate if too long
    if len(data_str) > max_length:
        data_str = data_str[:max_length] + "..."
    
    # Patterns to identify sensitive data
    sensitive_patterns = [
        r'password', r'passwd', r'pwd',
        r'secret', r'token', r'key',
        r'email', r'phone', r'address',
        r'credit', r'card', r'ssn',
        r'data', r'content', r'payload'
    ]
    
    # Check for sensitive patterns
    data_lower = data_str.lower()
    for pattern in sensitive_patterns:
        if re.search(pattern, data_lower):
            return "[SENSITIVE_DATA_REDACTED]"
    
    return data_str


def sanitize_file_path(file_path: str) -> str:
    """
    Sanitize file paths to remove sensitive directory information.
    
    Args:
        file_path: The file path to sanitize
        
    Returns:
        str: Sanitized file path safe for logging
    """
    if not file_path:
        return "[NO_PATH]"
    
    # Extract just the filename and a hash of the directory
    filename = os.path.basename(file_path)
    directory = os.path.dirname(file_path)
    
    # Create a hash of the directory for debugging without exposing the path
    dir_hash = hashlib.md5(directory.encode()).hexdigest()[:8]
    
    return f"[DIR_{dir_hash}]/{filename}"


def log_request_data_safely(data: dict, logger=None) -> None:
    """
    Log request data safely by sanitizing sensitive information.
    
    Args:
        data: Request data dictionary
        logger: Logger instance (optional)
    """
    if not data:
        return
    
    # Sanitize the data
    sanitized = {}
    for key, value in data.items():
        # Sanitize the key
        safe_key = sanitize_log_data(key, 20)
        
        # Sanitize the value
        if isinstance(value, (dict, list)):
            safe_value = "[COMPLEX_DATA_REDACTED]"
        else:
            safe_value = sanitize_log_data(str(value), 50)
        
        sanitized[safe_key] = safe_value
    
    if logger:
        logger.info(f"Request data (sanitized): {sanitized}")


def log_file_operation_safely(operation: str, file_path: str, logger=None) -> None:
    """
    Log file operations safely by sanitizing file paths.
    
    Args:
        operation: The operation being performed
        file_path: The file path (will be sanitized)
        logger: Logger instance (optional)
    """
    sanitized_path = sanitize_file_path(file_path)
    if logger:
        logger.info(f"File operation '{operation}': {sanitized_path}")


def log_security_event_safely(event_type: str, details: str = "", logger=None) -> None:
    """
    Log security events with appropriate detail level.
    
    Args:
        event_type: Type of security event
        details: Additional details (will be sanitized)
        logger: Logger instance (optional)
    """
    sanitized_details = sanitize_log_data(details, 100)
    if logger:
        logger.warning(f"SECURITY_EVENT: {event_type} - {sanitized_details}")


def log_error_safely(error: Exception, context: str = "", logger=None) -> None:
    """
    Log errors safely without exposing sensitive information.
    In production, only logs error type and sanitized message.
    In development, logs full details for debugging.
    
    Args:
        error: The exception to log
        context: Additional context (will be sanitized)
        logger: Logger instance (optional)
    """
    if not logger:
        return
    
    error_type = type(error).__name__
    error_message = str(error)
    
    # Check if we're in development mode
    is_development = os.getenv("FLASK_ENV", "production") == "development"
    
    if is_development:
        # In development, log full details for debugging
        logger.error(f"Error: {error_type} - {error_message} - Context: {context}")
    else:
        # In production, sanitize and limit error information
        sanitized_message = sanitize_log_data(error_message, 100)
        sanitized_context = sanitize_log_data(context, 50)
        logger.error(f"Error: {error_type} - {sanitized_message} - Context: {sanitized_context}")


def log_stack_trace_safely(error: Exception, logger=None) -> None:
    """
    Log stack traces safely based on environment.
    In production, logs minimal information.
    In development, logs full stack trace.
    
    Args:
        error: The exception to log
        logger: Logger instance (optional)
    """
    if not logger:
        return
    
    # Check if we're in development mode
    is_development = os.getenv("FLASK_ENV", "production") == "development"
    
    if is_development:
        # In development, log full stack trace for debugging
        import traceback
        logger.error(f"Full stack trace: {traceback.format_exc()}")
    else:
        # In production, log only essential information
        error_type = type(error).__name__
        logger.error(f"Error occurred: {error_type} - Stack trace redacted in production")