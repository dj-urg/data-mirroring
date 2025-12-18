from app import create_app
from app.utils.logging_config import setup_logging  # Import the logging function
import os

app = create_app()

setup_logging(app)

if __name__ == '__main__':
    is_debug = os.getenv('FLASK_ENV', 'production') == 'development'  # Debug only in development
    app.run(port=int(os.getenv('PORT', 5001)), host='0.0.0.0', debug=is_debug, threaded=True)