from app import create_app
from app.logging_config import setup_logging  # Import the logging function
import os
print(f"Current Working Directory: {os.getcwd()}")

app = create_app()

setup_logging(app)

if __name__ == '__main__':
    app.run(port=int(os.getenv('PORT', 5001)), host='0.0.0.0', debug=True, threaded=True)