
import pytest
from unittest.mock import patch, MagicMock
from app.utils.config import configure_app
from flask import Flask

def test_config_raises_error_without_access_code_hash():
    app = Flask(__name__)
    mock_logger = MagicMock()
    app.logger = mock_logger
    
    # Mock os.getenv to return None for ACCESS_CODE_HASH
    with patch.dict('os.environ', {}, clear=True):
        with pytest.raises(ValueError, match="ACCESS_CODE_HASH is not set"):
            configure_app(app)
            
def test_config_succeeds_with_access_code_hash():
    app = Flask(__name__)
    mock_logger = MagicMock()
    app.logger = mock_logger
    
    with patch.dict('os.environ', {'ACCESS_CODE_HASH': 'somehash'}, clear=True):
        try:
            configure_app(app)
        except ValueError:
            pytest.fail("configure_app raised ValueError unexpectedly!")
