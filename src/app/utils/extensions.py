from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os

# Determine the appropriate storage URI based on environment
def get_limiter_storage_uri():
    """Get the appropriate storage URI for rate limiting based on environment"""
    # In production, use file-based storage for persistence
    if os.getenv('FLASK_ENV', 'production') == 'production':
        # Create directory if it doesn't exist
        storage_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'rate_limits')
        os.makedirs(storage_dir, exist_ok=True)
        # Ensure directory has proper permissions
        os.chmod(storage_dir, 0o700)
        return f"filesystem://{storage_dir}"
    # In development, memory storage is acceptable
    return "memory://"

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=get_limiter_storage_uri()
)
