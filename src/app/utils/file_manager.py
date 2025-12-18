import os
import time
import tempfile
import shutil
import json
from flask import session, current_app
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
    MAX_FILE_AGE_SECONDS = 1800  # Maximum file age (30 minutes)

    @staticmethod
    def generate_secure_session_id():
        """
        Generate a cryptographically secure session identifier.
        
        Returns:
            str: Secure session identifier
        """
        return secrets.token_urlsafe(32)

    @classmethod
    def get_user_temp_dir(cls, create=True):
        """
        Create a secure, user-specific temporary directory.
        
        Args:
            create (bool): Whether to create the directory if it doesn't exist
            
        Returns:
            str: Path to the user's temporary directory
        """
        # Use a more secure session ID generation
        user_session_id = session.get('user_id') or cls.generate_secure_session_id()
        
        if not session.get('user_id'):
            session['user_id'] = user_session_id
        
        # Create a unique, secure temporary directory
        user_temp_dir = os.path.join(
            tempfile.gettempdir(), 
            f"user_{user_session_id}"
        )
        
        if not create:
            return user_temp_dir
        
        try:
            # Create directory with strict permissions if it doesn't exist
            if not os.path.exists(user_temp_dir):
                os.makedirs(user_temp_dir, mode=0o700, exist_ok=True)
            
            # Security note: We rely on directory permissions (0o700) 
            # rather than immutable flags for security
            
            return user_temp_dir
        
        except OSError as e:
            # Handle race condition where directory was created concurrently
            if e.errno == 17:  # File exists
                if os.path.isdir(user_temp_dir):
                    return user_temp_dir
                    
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
    def cleanup_temp_files(cls, _exception=None):
        """
        Enhanced cleanup with additional security checks.
        
        Args:
            _exception (Exception, optional): Exception from request processing (unused; required by teardown signature)
        """
        temp_dir = cls.get_user_temp_dir(create=False)
        current_time = time.time()
        
        try:
            # Race condition check: Ensure directory exists before listing
            if not os.path.exists(temp_dir):
                return

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
                            if os.path.exists(metadata_path):
                                os.remove(metadata_path)
                            
                            current_app.logger.info(f"Securely cleaned up expired file: {os.path.basename(item_path)}")
                    
                    except Exception as e:
                        current_app.logger.warning(f"Error processing cleanup for {item_path}: {e}")
        
        except FileNotFoundError:
            # Directory might have been removed by a concurrent request, which is fine
            pass
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
    def _secure_purge_directory(cls, dir_path: str, *, on_error=None, remove_self: bool = True) -> None:
        """
        Securely purge all contents of a directory and optionally remove the directory itself.

        Args:
            dir_path (str): Target directory to purge.
            on_error (Callable[[str], None] | None): Optional callback for error reporting.
                If provided, called with a human-readable message on any per-file error.
            remove_self (bool): When True, remove the directory after purging contents.
        """
        try:
            if not os.path.isdir(dir_path):
                return

            for entry in os.listdir(dir_path):
                file_path = os.path.join(dir_path, entry)
                try:
                    if os.path.isfile(file_path):
                        cls._secure_file_delete(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path, ignore_errors=True)
                except Exception as e:
                    if on_error:
                        on_error(f"Error deleting {file_path}: {e}")

            if remove_self:
                shutil.rmtree(dir_path, ignore_errors=True)
        except Exception as e:
            # Fallback reporting if a broader failure occurs and no callback supplied
            if on_error:
                on_error(f"Error purging directory {dir_path}: {e}")
            else:
                # Avoid relying on Flask logger here; this helper is used outside app context too
                print(f"Error purging directory {dir_path}: {e}")

    @classmethod
    def cleanup_all_temp_files(cls):
        """
        Clean up ALL temporary files on server startup.
        This ensures no user data persists through server restarts.
        """
        try:
            temp_base_dir = tempfile.gettempdir()
            print("Starting server startup cleanup of all temporary files")
            
            # Find all user_* directories in temp directory
            cleaned_count = 0
            for item in os.listdir(temp_base_dir):
                if item.startswith('user_'):
                    user_temp_dir = os.path.join(temp_base_dir, item)
                    
                    try:
                        if os.path.isdir(user_temp_dir):
                            # Securely purge the directory and remove it
                            cls._secure_purge_directory(
                                user_temp_dir,
                                on_error=lambda msg: print(msg),
                                remove_self=True,
                            )
                            cleaned_count += 1
                            print(f"Cleaned up orphaned user directory: {item}")
                    
                    except Exception as e:
                        print(f"Error cleaning up {user_temp_dir}: {e}")
            
            print(f"Server startup cleanup completed. Cleaned {cleaned_count} user directories")
            return cleaned_count
            
        except Exception as e:
            print(f"Server startup cleanup failed: {e}")
            return 0

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
                
                # Check for empty directory without aggressive removal to avoid race conditions
                # Directory will be cleaned up by periodic cleanup or session expiration
                temp_dir = cls.get_user_temp_dir(create=False)
                if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                     # Optional: could log empty state, but avoid rmtree here
                     pass
            
            except Exception as cleanup_error:
                current_app.logger.error(f"Final cleanup error: {cleanup_error}")

        # Enhanced session-based cleanup - immediate cleanup when session ends
        @app.before_request
        def check_session_cleanup():
            """Check for expired sessions and clean up immediately."""
            try:
                # Check if session is expired or invalid
                if not session.get('authenticated') and session.get('user_id'):
                    # Session ended, clean up immediately
                    user_id = session.get('user_id')
                    if user_id:
                        cls.cleanup_user_files_immediately(user_id)
                        # Don't clear session here - let it expire naturally
                
                # Also check for session expiration based on time
                import time
                if session.get('user_id') and session.get('last_activity'):
                    current_time = time.time()
                    last_activity = session.get('last_activity', 0)
                    session_timeout = 1800  # 30 minutes
                    
                    if current_time - last_activity > session_timeout:
                        # Session expired, clean up immediately
                        user_id = session.get('user_id')
                        if user_id:
                            cls.cleanup_user_files_immediately(user_id)
                            session.clear()
                else:
                    # Update last activity timestamp
                    session['last_activity'] = time.time()
                    
            except Exception as e:
                current_app.logger.error(f"Session cleanup check error: {e}")

        # Reduced periodic cleanup - only for server startup and edge cases
        import threading
        import time
        
        def periodic_cleanup():
            """Run periodic cleanup every 2 minutes for edge cases only."""
            while True:
                try:
                    time.sleep(120)  # 2 minutes (reduced from 5)
                    with app.app_context():
                        cls.cleanup_orphaned_files()
                except Exception as e:
                    with app.app_context():
                        app.logger.error(f"Periodic cleanup error: {e}")
        
        # Start periodic cleanup in a background thread
        cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
        cleanup_thread.start()
        app.logger.info("Enhanced session-based cleanup registered")

    @classmethod
    def cleanup_user_files_immediately(cls, user_id):
        """
        Immediately clean up all files for a specific user.
        This is called when a session ends to ensure immediate cleanup.
        
        Args:
            user_id (str): The user's session ID
        """
        try:
            temp_base_dir = tempfile.gettempdir()
            user_temp_dir = os.path.join(temp_base_dir, f"user_{user_id}")
            
            if os.path.exists(user_temp_dir) and os.path.isdir(user_temp_dir):
                # Securely delete all files in the directory
                for file_item in os.listdir(user_temp_dir):
                    file_path = os.path.join(user_temp_dir, file_item)
                    try:
                        if os.path.isfile(file_path):
                            cls._secure_file_delete(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path, ignore_errors=True)
                    except Exception as e:
                        current_app.logger.error(f"Error deleting {file_path}: {e}")
                
                # Remove the user directory itself
                shutil.rmtree(user_temp_dir, ignore_errors=True)
                current_app.logger.info(f"Immediate cleanup completed for user: {user_id}")
                
        except Exception as e:
            current_app.logger.error(f"Immediate user cleanup failed for {user_id}: {e}")

    @classmethod
    def cleanup_orphaned_files(cls):
        """
        Clean up orphaned files that may have been left behind.
        This runs periodically to catch any files that weren't cleaned up properly.
        """
        try:
            temp_base_dir = tempfile.gettempdir()
            current_time = time.time()
            cleaned_count = 0
            
            for item in os.listdir(temp_base_dir):
                if item.startswith('user_'):
                    user_temp_dir = os.path.join(temp_base_dir, item)
                    
                    try:
                        if os.path.isdir(user_temp_dir):
                            # Check if directory is older than 30 minutes (orphaned)
                            dir_age = current_time - os.path.getctime(user_temp_dir)
                            if dir_age > 1800:  # 30 minutes
                                # Securely purge the directory and remove it
                                cls._secure_purge_directory(
                                    user_temp_dir,
                                    on_error=lambda msg: print(msg),
                                    remove_self=True,
                                )
                                cleaned_count += 1
                                print(f"Cleaned up orphaned directory: {item}")
                    
                    except Exception as e:
                        print(f"Error cleaning up {user_temp_dir}: {e}")
            
            if cleaned_count > 0:
                print(f"Periodic cleanup completed. Cleaned {cleaned_count} orphaned directories")
            
        except Exception as e:
            print(f"Periodic cleanup failed: {e}")

# Convenience imports and functions
get_user_temp_dir = TemporaryFileManager.get_user_temp_dir
mark_file_for_cleanup = TemporaryFileManager.mark_file_for_cleanup
protect_file_for_download = TemporaryFileManager.protect_file_for_download