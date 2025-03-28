import os
import json
import logging
from werkzeug.utils import secure_filename
from flask import g
import magic  # python-magic package for MIME type detection

logger = logging.getLogger(__name__)

def sanitize_filename(filename):
    """
    Sanitize a filename to prevent path traversal and other security issues.
    
    Args:
        filename (str): The original filename
        
    Returns:
        str: A sanitized filename
    """
    if not filename:
        return None
        
    # Use werkzeug's secure_filename to remove dangerous characters
    sanitized = secure_filename(filename)
    
    if sanitized != filename:
        logger.warning(f"Filename sanitized: '{filename}' -> '{sanitized}'")
        
    return sanitized

def validate_file_size(file, max_size_mb=16):
    """
    Check if a file exceeds the maximum allowed size.
    
    Args:
        file: File-like object
        max_size_mb (int): Maximum file size in megabytes
        
    Returns:
        bool: True if file is valid, False otherwise
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    
    # Get file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer to beginning
    
    if file_size > max_size_bytes:
        logger.warning(f"File size check failed: {file_size} bytes exceeds limit of {max_size_bytes} bytes")
        return False
    
    return True

def validate_file_extension(filename, allowed_extensions=None):
    """
    Check if a file has an allowed extension.
    
    Args:
        filename (str): The filename to check
        allowed_extensions (list): List of allowed extensions (without dot)
        
    Returns:
        bool: True if extension is allowed or no restrictions specified
    """
    if not allowed_extensions:
        return True
        
    if not filename or '.' not in filename:
        return False
        
    ext = filename.rsplit('.', 1)[1].lower()
    
    if ext not in allowed_extensions:
        logger.warning(f"File extension check failed: '{ext}' not in allowed list: {allowed_extensions}")
        return False
        
    return True

def detect_content_type(file, max_check_size=8192):
    """
    Detect the MIME content type of a file.
    
    Args:
        file: File-like object
        max_check_size (int): Maximum number of bytes to read for detection
        
    Returns:
        str: Detected MIME type
    """
    # Save current position
    current_pos = file.tell()
    
    # Read bytes for content type detection
    file_content = file.read(max_check_size)
    
    # Reset to original position
    file.seek(current_pos)
    
    # Use python-magic to determine file type from content
    mime = magic.Magic(mime=True)
    content_type = mime.from_buffer(file_content)
    
    return content_type

def validate_content_type(file, expected_types):
    """
    Validate that a file's actual content matches expected types.
    
    Args:
        file: File-like object
        expected_types (list): List of allowed MIME types
        
    Returns:
        bool: True if content type is valid
    """
    detected_type = detect_content_type(file)
    
    if detected_type not in expected_types:
        logger.warning(f"Content type check failed: '{detected_type}' not in expected types: {expected_types}")
        return False
        
    return True

def get_mime_types_for_extension(ext):
    """
    Get expected MIME types for a given file extension.
    
    Args:
        ext (str): File extension without dot
        
    Returns:
        list: List of expected MIME types
    """
    mime_map = {
        # Data formats
        'json': ['application/json', 'text/plain'],
        'csv': ['text/csv', 'text/plain'],
        'xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
        'xls': ['application/vnd.ms-excel'],
        
        # Text formats
        'txt': ['text/plain'],
        'md': ['text/plain', 'text/markdown'],
        
        # Image formats
        'png': ['image/png'],
        'jpg': ['image/jpeg'],
        'jpeg': ['image/jpeg'],
        'gif': ['image/gif'],
        
        # Others
        'pdf': ['application/pdf'],
        'zip': ['application/zip', 'application/x-zip-compressed']
    }
    
    return mime_map.get(ext.lower(), [])

def validate_file(file, allowed_extensions=None, max_size_mb=16, validate_mime=True):
    """
    Comprehensive file validation.
    
    Args:
        file: File-like object with filename attribute
        allowed_extensions (list): List of allowed extensions
        max_size_mb (int): Maximum file size in megabytes
        validate_mime (bool): Whether to validate MIME type
        
    Returns:
        tuple: (is_valid, sanitized_filename, error_message)
    """
    if not file or not hasattr(file, 'filename') or file.filename == '':
        return False, None, "No file provided"
    
    # Check and sanitize filename
    original_filename = file.filename
    sanitized_filename = sanitize_filename(original_filename)
    
    if not sanitized_filename:
        return False, None, "Invalid filename"
    
    # Validate file size
    if not validate_file_size(file, max_size_mb):
        return False, sanitized_filename, f"File exceeds maximum size of {max_size_mb}MB"
    
    # Check file extension
    if allowed_extensions and not validate_file_extension(sanitized_filename, allowed_extensions):
        ext = sanitized_filename.rsplit('.', 1)[1].lower() if '.' in sanitized_filename else 'unknown'
        return False, sanitized_filename, f"File type '{ext}' not allowed. Allowed types: {', '.join(allowed_extensions)}"
    
    # Validate content type if requested
    if validate_mime and allowed_extensions:
        ext = sanitized_filename.rsplit('.', 1)[1].lower() if '.' in sanitized_filename else ''
        expected_types = get_mime_types_for_extension(ext)
        
        if expected_types and not validate_content_type(file, expected_types):
            return False, sanitized_filename, f"File content doesn't match its extension"
    
    return True, sanitized_filename, None

def safe_save_file(file, filename=None, directory=None):
    """
    Safely save a file to the specified directory with proper security checks.
    
    Args:
        file: File-like object
        filename (str): Optional sanitized filename (if not provided, will sanitize file.filename)
        directory (str): Target directory (if not provided, will use user temp dir)
        
    Returns:
        str: Full path to the saved file
    """
    from app.utils.file_manager import get_user_temp_dir
    
    # Use sanitized filename or sanitize the original
    safe_filename = filename or sanitize_filename(file.filename)
    
    # Use provided directory or get user temp dir
    save_dir = directory or get_user_temp_dir()
    
    # Ensure directory exists
    os.makedirs(save_dir, exist_ok=True)
    
    # Create full path
    file_path = os.path.join(save_dir, safe_filename)
    
    # Use realpath for additional security
    real_file_path = os.path.realpath(file_path)
    real_save_dir = os.path.realpath(save_dir)
    
    # Security check: ensure the resolved path is still within the target directory
    if not real_file_path.startswith(real_save_dir):
        logger.error(f"Path traversal attempt detected with filename: {safe_filename}")
        raise ValueError("Security error: Invalid file path")
    
    # Save the file
    file.save(real_file_path)
    logger.info(f"File saved securely at: {real_file_path}")
    
    # Register the file for automatic cleanup
    if hasattr(g, 'files_to_cleanup') and real_file_path not in g.files_to_cleanup:
        g.files_to_cleanup.append(real_file_path)
    
    # Set secure permissions
    os.chmod(real_file_path, 0o600)  # Owner read/write only
    
    return real_file_path

def parse_json_file(file, max_depth=20, max_keys=1000):
    """
    Safely parse a JSON file with security validations.
    
    Args:
        file: File-like object
        max_depth (int): Maximum nesting depth to prevent stack overflow attacks
        max_keys (int): Maximum number of keys to prevent DoS attacks
        
    Returns:
        tuple: (parsed_data, error_message)
    """
    # Reset file pointer
    file.seek(0)
    
    try:
        # Read the content
        content = file.read().decode('utf-8')
        
        # Check for circular references and excessive nesting
        def check_depth(obj, current_depth=0, key_count=0):
            if current_depth > max_depth:
                raise ValueError(f"JSON exceeds maximum nesting depth of {max_depth}")
                
            if key_count > max_keys:
                raise ValueError(f"JSON exceeds maximum number of keys ({max_keys})")
                
            if isinstance(obj, dict):
                new_key_count = key_count + len(obj)
                for k, v in obj.items():
                    check_depth(v, current_depth + 1, new_key_count)
            elif isinstance(obj, list):
                for item in obj:
                    check_depth(item, current_depth + 1, key_count)
        
        # Parse the JSON
        data = json.loads(content)
        
        # Check structure and limits
        check_depth(data)
        
        return data, None
        
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parsing error: {str(e)}")
        return None, f"Invalid JSON format: {str(e)}"
    except ValueError as e:
        logger.warning(f"JSON validation error: {str(e)}")
        return None, str(e)
    except Exception as e:
        logger.error(f"Unexpected error parsing JSON: {str(e)}")
        return None, "Error processing JSON file"

def process_uploaded_file(file, allowed_extensions=None, max_size_mb=16):
    """
    Process an uploaded file with validation and sanitization.
    
    Args:
        file: File-like object from request.files
        allowed_extensions (list): List of allowed file extensions
        max_size_mb (int): Maximum file size in megabytes
        
    Returns:
        tuple: (success, data_or_path, error_message)
            - success: Boolean indicating success
            - data_or_path: Parsed data (for JSON) or file path (for other types)
            - error_message: Error message if not successful
    """
    # Validate the file
    is_valid, sanitized_filename, error = validate_file(file, allowed_extensions, max_size_mb)
    
    if not is_valid:
        return False, None, error
    
    # Handle different file types based on extension
    if sanitized_filename.lower().endswith('.json'):
        # For JSON files, parse and return the data
        data, error = parse_json_file(file)
        if error:
            return False, None, error
        return True, data, None
    else:
        # For other files, save them and return the path
        try:
            file_path = safe_save_file(file, sanitized_filename)
            return True, file_path, None
        except Exception as e:
            return False, None, f"Error saving file: {str(e)}"