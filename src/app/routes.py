from flask import Blueprint, render_template, request, send_file, current_app, session, redirect, url_for, abort, g, jsonify
from app.utils.security import requires_authentication, enforce_https, apply_security_headers
from app.utils.file_manager import TemporaryFileManager, get_user_temp_dir
from app.utils.extensions import limiter
from app.utils.logging_config import log_request_data_safely, log_file_operation_safely, log_security_event_safely, log_error_safely, log_stack_trace_safely
from app.handlers.youtube import process_youtube_file
from app.handlers.instagram import process_instagram_file
from app.handlers.tiktok import process_tiktok_file

from app.utils.file_validation import validate_file
import os
from werkzeug.utils import secure_filename
import re
from flask import flash
from werkzeug.security import check_password_hash

routes_bp = Blueprint('routes', __name__)

routes_bp.before_request(enforce_https)
routes_bp.after_request(apply_security_headers)

@routes_bp.route('/robots.txt')
def robots():
    return current_app.send_static_file('robots.txt')

@limiter.limit("10 per minute", key_func=lambda: session.get('user_id', request.remote_addr))
@routes_bp.route('/')
@requires_authentication
def landing_page():
    current_app.logger.info("Landing page accessed.")
    return render_template('homepage.html')

@routes_bp.route('/platform-selection')
@requires_authentication
def platform_selection():
    current_app.logger.info("Platform selection page accessed.")
    return render_template('platform_selection.html')

@routes_bp.route('/info')
@requires_authentication
def info():
    current_app.logger.info("Info page accessed.")
    return render_template('info.html')

@routes_bp.route('/data_processing_info')
@requires_authentication
def data_processing_info():
    current_app.logger.info("Data processing info page accessed.")
    return render_template('data_processing_info.html')

@routes_bp.route('/generate_synthetic_data')
@requires_authentication
def generate_synthetic_data():
    current_app.logger.info("Generating synthetic data page accessed.")
    return render_template('generate_synthetic_data.html')

@routes_bp.route('/dashboard/youtube', methods=['GET', 'POST'])
@requires_authentication
@limiter.limit("10 per minute")
def dashboard_youtube():
    current_app.logger.info("Dashboard accessed for YouTube, Method: %s", request.method)

    if request.method == 'GET':
        current_app.logger.info("Rendering YouTube dashboard GET request.")
        return render_template('dashboard_youtube.html')

    current_app.logger.info("Handling POST request for YouTube dashboard.")

    files = request.files.getlist('file')
    if not files or files[0].filename == '':
        current_app.logger.warning("No files selected for upload.")
        flash("No file selected", "danger")
        return redirect(url_for('routes.dashboard_youtube'))

    current_app.logger.info("Number of files received: %d", len(files))
    
    # Validate files before processing
    valid_files = []
    for i, file in enumerate(files):
        current_app.logger.info("File %d: %s", i + 1, file.filename)
        
        is_valid, sanitized_name, error = validate_file(
            file,
            allowed_extensions=['json'],  # YouTube only accepts JSON
            max_size_mb=16  # 16MB max file size
        )
        
        if not is_valid:
            current_app.logger.warning(f"Invalid file: {error}")
            flash(f"Invalid file '{file.filename}': {error}", "danger")
            return redirect(url_for('routes.dashboard_youtube'))
            
        # Reset file pointer and add to valid files
        file.seek(0)
        valid_files.append(file)

    try:
        current_app.logger.info("Starting file processing...")

        df, excel_filename, csv_file_name, insights, plot_data, day_heatmap_data, month_heatmap_data, time_heatmap_data, has_valid_data, preview_data = process_youtube_file(valid_files)

        current_app.logger.info("File processing completed successfully.")

        return render_template(
            'dashboard_youtube.html',
            insights=insights,
            excel_filename=excel_filename,
            csv_file_name=csv_file_name,
            plot_data=plot_data,
            day_heatmap_data=day_heatmap_data,
            month_heatmap_data=month_heatmap_data,
            time_heatmap_data=time_heatmap_data,
            has_valid_data=has_valid_data,
            preview_data=preview_data
        )

    except ValueError as e:
        log_error_safely(e, "YouTube file processing", current_app.logger)
        flash(str(e), "danger")
        return redirect(url_for('routes.dashboard_youtube'))

    except Exception as e:
        log_error_safely(e, "Unexpected error during YouTube file processing", current_app.logger)
        log_stack_trace_safely(e, current_app.logger)
        flash("An unexpected error occurred during file processing. Please try again.", "danger")
        return redirect(url_for('routes.dashboard_youtube'))

@routes_bp.route('/dashboard/instagram', methods=['GET', 'POST'])
@requires_authentication
@limiter.limit("10 per minute")
def dashboard_instagram():
    current_app.logger.info("Dashboard accessed for Instagram, Method: %s", request.method)

    if request.method == 'GET':
        return render_template('dashboard_instagram.html')

    files = request.files.getlist('file')
    if not files or files[0].filename == '':
        flash("No file selected", "danger")
        return redirect(url_for('routes.dashboard_instagram'))
        
    current_app.logger.info("Processing %d file(s) for Instagram", len(files))
    
    valid_files = []
    for file in files:
        is_valid, sanitized_name, error = validate_file(
            file,
            allowed_extensions=['json'],  # Instagram only accepts JSON
            max_size_mb=16  # 16MB max file size
        )
        
        if not is_valid:
            current_app.logger.warning(f"Invalid file: {error}")
            flash(f"Invalid file '{file.filename}': {error}", "danger")
            return redirect(url_for('routes.dashboard_instagram'))
            
        # Reset file pointer and add to valid files
        file.seek(0)
        valid_files.append(file)

    try:
        df, csv_file_name, insights, bump_chart_name, day_heatmap_name, month_heatmap_name, time_heatmap_name, preview_data, has_valid_data = process_instagram_file(valid_files)

        return render_template(
            'dashboard_instagram.html',
            insights=insights,
            csv_file_name=csv_file_name,
            plot_data=bump_chart_name,
            day_heatmap_data=day_heatmap_name,
            month_heatmap_data=month_heatmap_name,
            time_heatmap_data=time_heatmap_name,
            has_valid_data=has_valid_data,
            preview_data=preview_data
        )
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for('routes.dashboard_instagram'))

@routes_bp.route('/dashboard/tiktok', methods=['GET', 'POST'])
@requires_authentication
@limiter.limit("10 per minute")
def dashboard_tiktok():
    current_app.logger.info("Dashboard accessed for TikTok, Method: %s", request.method)
    
    if request.method == 'GET':
        return render_template('dashboard_tiktok.html')
    
    files = request.files.getlist('file')
    if not files or files[0].filename == '':
        flash("No file selected", "danger")
        return redirect(url_for('routes.dashboard_tiktok'))
    
    current_app.logger.info("Processing %d file(s) for TikTok", len(files))
    
    # Validate files before processing
    from app.utils.file_validation import validate_file
    
    valid_files = []
    for file in files:
        is_valid, sanitized_name, error = validate_file(
            file,
            allowed_extensions=['json'],  # TikTok only accepts JSON
            max_size_mb=16  # 16MB max file size
        )
        
        if not is_valid:
            current_app.logger.warning(f"Invalid file: {error}")
            flash(f"Invalid file '{file.filename}': {error}", "danger")
            return redirect(url_for('routes.dashboard_tiktok'))
            
        # Reset file pointer and add to valid files
        file.seek(0)
        valid_files.append(file)
    
    try:
        df, csv_file_name, excel_file_name, url_file_name, insights, day_heatmap_name, time_heatmap_name, month_heatmap_name, has_valid_data, preview_data = process_tiktok_file(valid_files)

        return render_template(
            'dashboard_tiktok.html',
            insights=insights,
            csv_file_name=csv_file_name,
            excel_file_name=excel_file_name,
            url_file_name=url_file_name,
            day_heatmap_name=day_heatmap_name,
            time_heatmap_name=time_heatmap_name,
            month_heatmap_name=month_heatmap_name,
            has_valid_data=has_valid_data,
            preview_data=preview_data
        )
        
    except ValueError as e:
        log_error_safely(e, "TikTok file processing", current_app.logger)
        flash(str(e), "danger")
        return redirect(url_for('routes.dashboard_tiktok'))
    
@routes_bp.route('/dashboard/netflix')
@requires_authentication
def dashboard_netflix():
    current_app.logger.info("Dashboard accessed for Netflix (Local Mode).")
    return render_template('dashboard_netflix.html')

@routes_bp.route('/download_image/<filename>', methods=['GET'])
@requires_authentication
@limiter.exempt
def download_image(filename):
    """Serve the requested image file for download and delete it after sending."""
    
    # Sanitize filename to prevent directory traversal attacks
    safe_filename = secure_filename(filename)

    # Define temp directory
    temp_dir = get_user_temp_dir()
    temp_file_path = os.path.join(temp_dir, safe_filename)

    # Use realpath instead of normpath for stronger path traversal protection
    temp_file_path = os.path.realpath(temp_file_path)
    temp_dir = os.path.realpath(temp_dir)

    # Ensure the file is only served from the temp directory
    if not temp_file_path.startswith(temp_dir):
        log_security_event_safely("blocked_file_access", f"filename: {filename}", current_app.logger)
        abort(400, "Invalid file request")

    if os.path.exists(temp_file_path):
        try:
            # Add file to the list of files to clean up at the end of the request
            if not hasattr(g, 'files_to_cleanup'):
                g.files_to_cleanup = []
            if temp_file_path not in g.files_to_cleanup:
                g.files_to_cleanup.append(temp_file_path)
                
            response = send_file(temp_file_path, mimetype="image/png")

            # Still try to delete after the response is sent (primary cleanup)
            @response.call_on_close
            def remove_temp_file():
                try:
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                        # If successfully deleted, remove from the cleanup list
                        if hasattr(g, 'files_to_cleanup') and temp_file_path in g.files_to_cleanup:
                            g.files_to_cleanup.remove(temp_file_path)
                        log_file_operation_safely("file_deleted", temp_file_path, current_app.logger)
                except Exception as e:
                    current_app.logger.error(f"Failed to delete file {temp_file_path}: {e}")

            return response
        except Exception as e:
            # Try to clean up on error too
            try:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    if hasattr(g, 'files_to_cleanup') and temp_file_path in g.files_to_cleanup:
                        g.files_to_cleanup.remove(temp_file_path)
            except:
                pass  # Already logging in teardown_request
                
            current_app.logger.error(f"Error serving file {temp_file_path}: {e}")
            abort(500, "Internal server error")
    else:
        current_app.logger.warning(f"Attempted access to a non-existent file.")
        abort(404, "File not found")

@routes_bp.route('/download_csv/<filename>', methods=['GET'])
@requires_authentication
@limiter.exempt
def download_csv(filename):
    """Serve the requested CSV file for download and delete it immediately after."""

    # Sanitize filename to prevent directory traversal attacks
    safe_filename = secure_filename(filename)

    # Define temp directory
    temp_dir = get_user_temp_dir()  # Now imported from file_manager
    temp_file_path = os.path.join(temp_dir, safe_filename)

    # Use realpath instead of normpath for stronger path traversal protection
    temp_file_path = os.path.realpath(temp_file_path)
    temp_dir = os.path.realpath(temp_dir)

    # Ensure the file is only accessed from the temp directory
    if not temp_file_path.startswith(temp_dir):
        log_security_event_safely("blocked_file_access", f"filename: {filename}", current_app.logger)
        abort(400, "Invalid file request")

    if os.path.exists(temp_file_path):
        try:
            # Protect the file from immediate deletion
            TemporaryFileManager.protect_file_for_download(temp_file_path)
                
            response = send_file(temp_file_path, as_attachment=True, download_name=safe_filename, mimetype="text/csv")

            # Still try to delete after the response is sent (primary cleanup)
            @response.call_on_close
            def remove_temp_file():
                try:
                    if os.path.exists(temp_file_path):
                        # Mark the file for cleanup
                        TemporaryFileManager.mark_file_for_cleanup(temp_file_path)
                        log_file_operation_safely("file_marked_for_deletion", temp_file_path, current_app.logger)
                except Exception as e:
                    current_app.logger.error(f"Failed to mark file {temp_file_path} for deletion: {e}")

            return response
        except Exception as e:
            # Try to clean up on error too
            try:
                if os.path.exists(temp_file_path):
                    TemporaryFileManager.mark_file_for_cleanup(temp_file_path)
            except:
                pass  # Already logging in teardown_request
                
            current_app.logger.error(f"Error serving file {temp_file_path}: {e}")
            abort(500, "Internal server error")
    else:
        current_app.logger.warning(f"File not found: {temp_file_path}")
        abort(404, "File not found")
    
def is_valid_code(code):
    """
    Ensure the code has a reasonable length and valid characters.
    """
    # Allow alphanumeric and common special characters, min length 1 (flexible for user preference)
    # Ideally should be 8+ for security, but we allow 'test' as requested.
    return bool(re.match(r'^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};:\'",.<>/?]{1,50}$', code))

@routes_bp.route('/enter-code', methods=['GET', 'POST'])
@limiter.limit("5 per minute") 
def enter_code():
    ACCESS_CODE_HASH = os.getenv('ACCESS_CODE_HASH')
    
    if request.method == 'POST':
        code = request.form.get('code')

        # Validate the input code format before comparing
        if not code or not is_valid_code(code):
            current_app.logger.warning(f"Invalid password format attempt from {request.remote_addr}")
            return render_template('enter_code.html', error="Invalid access code format.")
        
        # Verify the password hash
        if ACCESS_CODE_HASH and check_password_hash(ACCESS_CODE_HASH, code):
            session.clear() # Clear any existing session data to prevent fixation
            session['authenticated'] = True  # Set authenticated status in session
            
            # Explicitly generate a secure session ID for the user
            # This ensures consistent identification for rate limiting and file management
            session['user_id'] = TemporaryFileManager.generate_secure_session_id()
            log_security_event_safely("LOGIN_SUCCESS", f"User logged in from {request.remote_addr}", current_app.logger)
            return redirect(url_for('routes.landing_page'))
        else:
            current_app.logger.warning(f"Failed login attempt from {request.remote_addr}")
            return render_template('enter_code.html', error="Invalid access code.")
    
    return render_template('enter_code.html')

@routes_bp.route('/logout')
def logout():
    """Explicitly clear all session data and user files."""
    try:
        # Get user ID before clearing session
        user_id = session.get('user_id')
        
        if user_id:
            # Clean up user's temporary files immediately
            from app.utils.file_manager import TemporaryFileManager
            TemporaryFileManager.cleanup_user_files_immediately(user_id)
            
        # Clear all session data
        session.clear()
        
        current_app.logger.info(f"User logout: session cleared for user {user_id}")
        
        current_app.logger.info("User logged out and all data cleared")
        return redirect(url_for('routes.enter_code'))
        
    except Exception as e:
        current_app.logger.error(f"Logout cleanup error: {e}")
        # Still redirect even if cleanup fails
        return redirect(url_for('routes.enter_code'))

@routes_bp.route('/cleanup-session', methods=['POST'])
def cleanup_session():
    """Handle cleanup requests from client-side (browser close, etc.)."""
    try:
        from app.utils.file_manager import TemporaryFileManager
        
        # Get user ID from session
        user_id = session.get('user_id')
        if user_id:
            # Immediately clean up user files
            TemporaryFileManager.cleanup_user_files_immediately(user_id)
            current_app.logger.info(f"Client-triggered cleanup completed for user: {user_id}")
        
        return jsonify({"status": "success", "message": "Cleanup completed"})
        
    except Exception as e:
        current_app.logger.error(f"Client cleanup error: {e}")
        return jsonify({"status": "error", "message": "Cleanup failed"}), 500

@routes_bp.route('/download_excel/<filename>', methods=['GET'])
@requires_authentication
@limiter.exempt
def download_excel(filename):
    """Serve the requested Excel file for download and delete it immediately after."""

    # Sanitize filename to prevent directory traversal attacks
    safe_filename = secure_filename(filename)

    # Define temp directory
    temp_dir = get_user_temp_dir()
    temp_file_path = os.path.join(temp_dir, safe_filename)

    # Use realpath instead of normpath for stronger path traversal protection
    temp_file_path = os.path.realpath(temp_file_path)
    temp_dir = os.path.realpath(temp_dir)

    # Ensure the file is only accessed from the temp directory
    if not temp_file_path.startswith(temp_dir):
        log_security_event_safely("blocked_file_access", f"filename: {filename}", current_app.logger)
        abort(400, "Invalid file request")

    if os.path.exists(temp_file_path):
        try:
            # Add file to the list of files to clean up at the end of the request
            if not hasattr(g, 'files_to_cleanup'):
                g.files_to_cleanup = []
            if temp_file_path not in g.files_to_cleanup:
                g.files_to_cleanup.append(temp_file_path)
                
            response = send_file(temp_file_path, as_attachment=True, download_name=safe_filename, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            # Still try to delete after the response is sent (primary cleanup)
            @response.call_on_close
            def remove_temp_file():
                try:
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                        # If successfully deleted, remove from the cleanup list
                        if hasattr(g, 'files_to_cleanup') and temp_file_path in g.files_to_cleanup:
                            g.files_to_cleanup.remove(temp_file_path)
                        log_file_operation_safely("file_deleted", temp_file_path, current_app.logger)
                except Exception as e:
                    current_app.logger.error(f"Failed to delete file {temp_file_path}: {e}")

            return response
        except Exception as e:
            # Try to cleanup on error too
            try:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    if hasattr(g, 'files_to_cleanup') and temp_file_path in g.files_to_cleanup:
                        g.files_to_cleanup.remove(temp_file_path)
            except:
                pass  # Already logging in teardown_request
                
            current_app.logger.error(f"Error serving file {temp_file_path}: {e}")
            abort(500, "Internal server error")
    else:
        current_app.logger.warning(f"File not found: {temp_file_path}")
        abort(404, "File not found")

@routes_bp.route('/download_txt/<filename>', methods=['GET'])
@requires_authentication
@limiter.exempt
def download_txt(filename):
    """Serve the requested text file for download and delete it immediately after."""

    # Sanitize filename to prevent directory traversal attacks
    safe_filename = secure_filename(filename)

    # Define temp directory
    temp_dir = get_user_temp_dir()
    temp_file_path = os.path.join(temp_dir, safe_filename)

    # Use realpath instead of normpath for stronger path traversal protection
    temp_file_path = os.path.realpath(temp_file_path)
    temp_dir = os.path.realpath(temp_dir)

    # Ensure the file is only accessed from the temp directory
    if not temp_file_path.startswith(temp_dir):
        log_security_event_safely("blocked_file_access", f"filename: {filename}", current_app.logger)
        abort(400, "Invalid file request")

    if os.path.exists(temp_file_path):
        try:
            # Add file to the list of files to clean up at the end of the request
            if not hasattr(g, 'files_to_cleanup'):
                g.files_to_cleanup = []
            if temp_file_path not in g.files_to_cleanup:
                g.files_to_cleanup.append(temp_file_path)
                
            response = send_file(temp_file_path, as_attachment=True, download_name="tiktok_urls.txt", mimetype="text/plain")

            # Still try to delete after the response is sent (primary cleanup)
            @response.call_on_close
            def remove_temp_file():
                try:
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                        # If successfully deleted, remove from the cleanup list
                        if hasattr(g, 'files_to_cleanup') and temp_file_path in g.files_to_cleanup:
                            g.files_to_cleanup.remove(temp_file_path)
                        log_file_operation_safely("file_deleted", temp_file_path, current_app.logger)
                except Exception as e:
                    current_app.logger.error(f"Failed to delete file {temp_file_path}: {e}")

            return response
        except Exception as e:
            # Try to cleanup on error too
            try:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    if hasattr(g, 'files_to_cleanup') and temp_file_path in g.files_to_cleanup:
                        g.files_to_cleanup.remove(temp_file_path)
            except:
                pass  # Already logging in teardown_request
                
            current_app.logger.error(f"Error serving file {temp_file_path}: {e}")
            abort(500, "Internal server error")
    else:
        current_app.logger.warning(f"File not found: {temp_file_path}")
        abort(404, "File not found")
        
@routes_bp.route('/generate_synthetic_data_api', methods=['POST'])
@requires_authentication
@limiter.limit("10 per minute")
def generate_synthetic_data_api():
    from app.handlers.generate_synthetic_data import generate_synthetic_data
    from flask import jsonify, request, current_app
    
    try:
        current_app.logger.info("Synthetic data generation API called")
        
        # Parse input from request
        data = request.get_json()
        log_request_data_safely(data, current_app.logger)
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        persona_type = data.get('persona_type')
        activity_level = data.get('activity_level')
        output_filename = data.get('output_filename')
        platform = data.get('platform', 'instagram') # Default to instagram
        
        if not all([persona_type, activity_level, output_filename]):
            return jsonify({"error": "Missing required fields"}), 400
            
        # Security: Allowlist check is done inside generate_synthetic_data
        # We just pass the simple filename, the handler will secure it and put it in temp dir
        
        current_app.logger.info(f"Generating data for {persona_type} ({activity_level}) - {output_filename} on {platform}")
        
        # Generate the data
        # output_filename here is just the name like 'liked_posts.json'. 
        # The function will return the full path if successful.
        result = generate_synthetic_data(persona_type, activity_level, output_filename, platform=platform)
        
        if not result:
            return jsonify({"error": "Failed to generate data. Security check failed or invalid parameters."}), 500
            
        # The result contains stats and the data itself
        # We need to extract the filename for the download link
        final_filename = output_filename
            
        stats = result.get('stats', {})
        
        return jsonify({
            "status": "success",
            "filename": final_filename,
            "total_items": stats.get('total_items', 0),
            "stats": stats
        })
        
    except Exception as e:
        # Log the error safely based on environment
        log_error_safely(e, "Synthetic data generation", current_app.logger)
        log_stack_trace_safely(e, current_app.logger)
        
        # Return a generic error message to the user
        return jsonify({"error": "An internal error occurred while processing your request"}), 500

@routes_bp.route('/download/<filename>', methods=['GET'])
@requires_authentication
@limiter.exempt
def download_generated_file(filename):
    """Serve the generated file for download."""
    # Sanitize filename to prevent directory traversal attacks
    safe_filename = secure_filename(filename)

    # Define temp directory
    temp_dir = get_user_temp_dir()
    temp_file_path = os.path.join(temp_dir, safe_filename)

    # Use realpath for stronger path traversal protection
    temp_file_path = os.path.realpath(temp_file_path)
    temp_dir = os.path.realpath(temp_dir)

    # Ensure the file is only accessed from the temp directory
    if not temp_file_path.startswith(temp_dir):
        log_security_event_safely("blocked_file_access", f"filename: {filename}", current_app.logger)
        abort(400, "Invalid file request")

    if os.path.exists(temp_file_path):
        try:
            # Add file to the list of files to clean up at the end of the request
            if not hasattr(g, 'files_to_cleanup'):
                g.files_to_cleanup = []
            if temp_file_path not in g.files_to_cleanup:
                g.files_to_cleanup.append(temp_file_path)
                
            # Determine content type based on file extension
            content_type = "application/json" if filename.endswith('.json') else "text/plain"
                
            response = send_file(temp_file_path, 
                                as_attachment=True, 
                                download_name=safe_filename, 
                                mimetype=content_type)

            # Try to delete after the response is sent
            @response.call_on_close
            def remove_temp_file():
                try:
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                        # If successfully deleted, remove from the cleanup list
                        if hasattr(g, 'files_to_cleanup') and temp_file_path in g.files_to_cleanup:
                            g.files_to_cleanup.remove(temp_file_path)
                        log_file_operation_safely("file_deleted", temp_file_path, current_app.logger)
                except Exception as e:
                    current_app.logger.error(f"Failed to delete file {temp_file_path}: {e}")

            return response
        except Exception as e:
            # Try to cleanup on error too
            try:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    if hasattr(g, 'files_to_cleanup') and temp_file_path in g.files_to_cleanup:
                        g.files_to_cleanup.remove(temp_file_path)
            except:
                pass
                
            current_app.logger.error(f"Error serving file {temp_file_path}: {e}")
            abort(500, "Internal server error")
    else:
        current_app.logger.warning(f"File not found: {temp_file_path}")
        abort(404, "File not found")
