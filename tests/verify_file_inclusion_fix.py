import os
import tempfile
from app.utils.file_manager import TemporaryFileManager
from flask import Flask, current_app

def verify_fix():
    app = Flask(__name__)
    
    with app.app_context():
        # Setup
        temp_dir = tempfile.gettempdir()
        safe_file_path = os.path.join(temp_dir, 'safe_file.txt')
        dangerous_file_path = os.path.abspath('dangerous_file.txt')
        
        # Ensure dummy files exist
        with open(safe_file_path, 'w') as f:
            f.write("safe content")
            
        with open(dangerous_file_path, 'w') as f:
            f.write("dangerous content")
            
        try:
            print(f"Testing safe file: {safe_file_path}")
            safe_hash = TemporaryFileManager._generate_file_hash(safe_file_path)
            if safe_hash:
                print("SUCCESS: Safe file processed correctly.")
            else:
                print("FAILURE: Safe file was blocked or failed.")

            print(f"Testing dangerous file: {dangerous_file_path}")
            dangerous_hash = TemporaryFileManager._generate_file_hash(dangerous_file_path)
            if dangerous_hash is None:
                print("SUCCESS: Dangerous file was correctly blocked.")
            else:
                print(f"FAILURE: Dangerous file was NOT blocked. Hash: {dangerous_hash}")

        finally:
            # Cleanup
            if os.path.exists(safe_file_path):
                os.remove(safe_file_path)
            if os.path.exists(dangerous_file_path):
                os.remove(dangerous_file_path)

if __name__ == "__main__":
    verify_fix()
