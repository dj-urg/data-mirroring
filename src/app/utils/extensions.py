from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Create Limiter without specifying storage options - these will be set in __init__.py
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)