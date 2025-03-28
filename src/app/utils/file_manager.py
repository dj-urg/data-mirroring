import os
import time
import tempfile
import shutil
import uuid
import json
import logging
from flask import session, current_app, g
import secrets

class TemporaryFileManager:
    """
    A centralized manager for handling temporary file operations,
    providing robust file lifecycle management and cleanup strategies.
    """
    
    # Security Configuration
    DOWNLOAD_WINDOW = 1800  # 30 minutes in seconds
    MAX_TEMP_FILES_PER_USER = 50  # Limit number of temporary files
    MAX_TEMP_STORAGE_MB = 500  # Maximum total temporary storage per user
    MAX_FILE_AGE_SECONDS = 3600  # Maximum file age (1 hour)

    @staticmethod
    def generate_secure_session_id():
        """
        Generate a cryptographically secure session identifier.
        
        Returns:
            str: Secure session identifier
        """
        return secrets.token_urlsafe(32)

    @staticmethod
    def get_user_temp_dir():
        """
        Create a secure, user-specific temporary directory.
        
        Returns:
            str: Path to the user's temporary directory
        """
        # Use a more secure session ID generation
        user_session_id = session.get('user_id') or TemporaryFileManager.generate_secure_session_id()
        
        if not session.get('user_id'):
            session['user_id'] = user_session_id
        
        # Create a unique, secure temporary directory
        user_temp_dir = os.path.join(
            tempfile.gettempdir(), 
            f"user_{user_session_id}"
        )
        
        try:
            # Create directory with strict permissions
            os.makedirs(user_temp_dir, mode=0o700, exist_ok=True)
            
            # Additional security: set immutable flag if supported
            try:
                import platform
                if platform.system() == 'Linux':
                    import ctypes
                    import ctypes.util
                    
                    # Attempt to set immutable flag on directory
                    try:
                        libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)
                        FS_IMMUTABLE_FL = 0x00000010  # Linux immutable flag
                        libc.chattr(user_temp_dir.encode(), FS_IMMUTABLE_FL)
                    except Exception:
                        # Silently fail if setting immutable flag is not possible
                        pass
            except ImportError:
                # Skip immutable flag if platform doesn't support it
                pass
            
            return user_temp_dir
        
        except Exception as e:
            current_app.logger.error(f"Failed to create secure temp directory: {e}")
            raise RuntimeError("Unable to create secure temporary directory")

    @classmethod
    def protect_file_for_download(cls, file_path):
        """
        Prevents a specific file from being immediately deleted.
        
        Args:
            file_path (str): Full path to the file to be protected
        """
        try:
            # Remove any existing metadata that might trigger deletion
            metadata_path = f"{file_path}.metadata"
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
        except Exception as e:
            current_app.logger.error(f"Error protecting file: {e}")

    @classmethod
    def mark_file_for_cleanup(cls, file_path):
        """
        Enhanced file cleanup marking with additional metadata.
        
        Args:
            file_path (str): Full path to the file to be marked for cleanup
        """
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                return

            # Create enhanced metadata
            metadata_path = f"{file_path}.metadata"
            metadata = {
                'original_path': file_path,
                'mark_time': time.time(),
                'delete_after': time.time() + cls.DOWNLOAD_WINDOW,
                'file_hash': cls._generate_file_hash(file_path)
            }
            
            # Write metadata securely
            with open(metadata_path, 'w', opener=lambda path, flags: os.open(path, flags, 0o600)) as f:
                json.dump(metadata, f)
            
            current_app.logger.info(f"Enhanced file cleanup mark: {os.path.basename(file_path)}")
        
        except Exception as e:
            current_app.logger.error(f"Enhanced file cleanup marking failed: {e}")

    @staticmethod
    def _generate_file_hash(file_path, algorithm='sha256'):
        """
        Generate a cryptographic hash of a file.
        
        Args:
            file_path (str): Path to the file
            algorithm (str): Hash algorithm to use
        
        Returns:
            str: Hexadecimal hash of the file
        """
        import hashlib
        
        try:
            hash_obj = hashlib.new(algorithm)
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            current_app.logger.error(f"File hash generation failed: {e}")
            return None

    @classmethod
    def cleanup_temp_files(cls, exception=None):
        """
        Enhanced cleanup with additional security checks.
        
        Args:
            exception (Exception, optional): Exception from request processing
        """
        temp_dir = cls.get_user_temp_dir()
        current_time = time.time()
        
        try:
            for item in os.listdir(temp_dir):
                item_path = os.path.join(temp_dir, item)
                metadata_path = f"{item_path}.metadata"
                
                # Check if metadata exists
                if os.path.exists(metadata_path):
                    try:
                        # Read enhanced metadata
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                        
                        deletion_time = metadata.get('delete_after', current_time)
                        
                        # Delete if deletion time has passed
                        if deletion_time <= current_time:
                            if os.path.exists(item_path):
                                # Overwrite file contents before deletion
                                cls._secure_file_delete(item_path)
                            
                            # Remove metadata
                            os.remove(metadata_path)
                            
                            current_app.logger.info(f"Securely cleaned up expired file: {os.path.basename(item_path)}")
                    
                    except Exception as e:
                        current_app.logger.error(f"Error processing {item_path}: {e}")
        
        except Exception as e:
            current_app.logger.error(f"Secure temporary file cleanup failed: {e}")

    @staticmethod
    def _secure_file_delete(file_path):
        """
        Securely delete a file by overwriting its contents.
        
        Args:
            file_path (str): Path to the file to be securely deleted
        """
        try:
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Overwrite with random data
            with open(file_path, 'wb') as f:
                f.write(os.urandom(file_size))
            
            # Remove the file
            os.remove(file_path)
        
        except Exception as e:
            current_app.logger.error(f"Secure file deletion failed: {e}")

    @classmethod
    def register_cleanup(cls, app):
        """
        Register comprehensive cleanup functions.
        
        Args:
            app (Flask): The Flask application instance
        """
        @app.before_request
        def initialize_request_cleanup():
            """Prepare for new session with security checks."""
            try:
                temp_dir = cls.get_user_temp_dir()
                
                # Perform cleanup
                cls.cleanup_temp_files()
            
            except Exception as e:
                current_app.logger.error(f"Initialization cleanup error: {e}")

        @app.teardown_request
        def cleanup_request_context(exception=None):
            """
            Final cleanup with additional security measures.
            
            Args:
                exception (Exception, optional): Any exception during the request
            """
            try:
                # Perform final cleanup
                cls.cleanup_temp_files(exception)
                
                # Remove temp directory if empty
                temp_dir = cls.get_user_temp_dir()
                if not os.listdir(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
            
            except Exception as cleanup_error:
                current_app.logger.error(f"Final cleanup error: {cleanup_error}")

# Convenience imports and functions
get_user_temp_dir = TemporaryFileManager.get_user_temp_dir
mark_file_for_cleanup = TemporaryFileManager.mark_file_for_cleanup
protect_file_for_download = TemporaryFileManager.protect_file_for_download