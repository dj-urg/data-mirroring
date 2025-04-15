from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# In extensions.py
limiter = Limiter(
    storage_options={"uri": "memory"},  # This will be overridden
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)