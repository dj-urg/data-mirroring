from flask import Blueprint, render_template, request, send_file, current_app, session, redirect, url_for, abort
from app.utils.security import requires_authentication, cleanup_old_temp_files, enforce_https, apply_security_headers, cleanup_temp_files
from app.utils.extensions import limiter
from app.utils.file_utils import get_user_temp_dir
from app.handlers.youtube import process_youtube_file
from app.handlers.instagram import process_instagram_file
from app.handlers.tiktok import process_tiktok_file
import os
import jsonify
import tempfile
from werkzeug.utils import secure_filename
import re
from flask import flash

routes_bp = Blueprint('routes', __name__)

# Register security functions with Flask
routes_bp.before_request(cleanup_old_temp_files)
routes_bp.before_request(cleanup_temp_files)
routes_bp.before_request(enforce_https)
routes_bp.after_request(apply_security_headers)  # Apply security headers to responses
routes_bp.teardown_request(cleanup_old_temp_files)  # Runs after each request

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
        flash("No file selected", "danger")  # Keep the flash message
        return redirect(url_for('routes.dashboard_youtube'))

    current_app.logger.info("Number of files received: %d", len(files))
    for i, file in enumerate(files):
        current_app.logger.info("File %d: %s", i + 1, file.filename)

    try:
        current_app.logger.info("Starting file processing...")

        df, excel_filename, csv_file_name, insights, plot_data, day_heatmap_data, month_heatmap_data, time_heatmap_data, has_valid_data, csv_preview_html = process_youtube_file(files)

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
            csv_preview_html=csv_preview_html
        )

    except ValueError as e:
        current_app.logger.error("ValueError encountered during processing: %s", str(e))
        flash(str(e), "danger")  # Keep flash messages for errors
        return redirect(url_for('routes.dashboard_youtube'))

    except Exception as e:
        current_app.logger.error("Unexpected error during file processing: %s", str(e))
        flash("An unexpected error occurred during file processing. Please try again.", "danger")
        return redirect(url_for('routes.dashboard_youtube'))

@routes_bp.route('/dashboard/instagram', methods=['GET', 'POST'])
@requires_authentication
@limiter.limit("10 per minute")
def dashboard_instagram():
    current_app.logger.info("Dashboard accessed for Instagram, Method: %s", request.method,)

    if request.method == 'GET':
        return render_template('dashboard_instagram.html')

    files = request.files.getlist('file')
    current_app.logger.info("Processing %d file(s) for Instagram", len(files))

    try:
        df, csv_file_name, insights, bump_chart_name, day_heatmap_name, month_heatmap_name, time_heatmap_name, csv_preview_html, has_valid_data = process_instagram_file(files)

        return render_template(
            'dashboard_instagram.html',
            insights=insights,
            csv_file_name=csv_file_name,
            plot_data=bump_chart_name,
            day_heatmap_data=day_heatmap_name,
            month_heatmap_data=month_heatmap_name,
            time_heatmap_data=time_heatmap_name,
            has_valid_data=has_valid_data,
            csv_preview_html=csv_preview_html
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
    
    try:
        df, csv_file_name, excel_file_name, url_file_name, insights, day_heatmap_name, time_heatmap_name, month_heatmap_name, has_valid_data, csv_preview_html = process_tiktok_file(files)
        
        data_html = df.to_html(classes="table table-bordered table-hover") if has_valid_data else None
        
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
            csv_preview_html=csv_preview_html
        )
        
    except ValueError as e:
        flash(str(e), "danger")
        current_app.logger.error("Error processing TikTok file: %s", str(e))
        return redirect(url_for('routes.dashboard_tiktok'))
    
@routes_bp.route('/download_image/<filename>', methods=['GET'])
def download_image(filename):
    """Serve the requested image file for download and delete it after sending."""
    
    # Sanitize filename to prevent directory traversal attacks
    safe_filename = secure_filename(filename)

    # Define temp directory
    temp_dir = get_user_temp_dir()
    temp_file_path = os.path.join(temp_dir, safe_filename)

    # Normalize path to prevent path traversal
    temp_file_path = os.path.normpath(temp_file_path)

    # Ensure the file is only served from the temp directory
    if not temp_file_path.startswith(temp_dir):
        current_app.logger.warning(f"Blocked attempt to access an invalid file")
        abort(400, "Invalid file request")

    if os.path.exists(temp_file_path):
        try:
            response = send_file(temp_file_path, mimetype="image/png")

            # Delete AFTER the response is fully sent
            @response.call_on_close
            def remove_temp_file():
                try:
                    os.remove(temp_file_path)
                    current_app.logger.info(f"Deleted temporary file: {temp_file_path}")
                except Exception as e:
                    current_app.logger.error(f"Failed to delete file {temp_file_path}: {e}")

            return response
        except Exception as e:
            current_app.logger.error(f"Error serving file {temp_file_path}: {e}")
            abort(500, "Internal server error")
    else:
        current_app.logger.warning(f"Attempted access to a non-existent file.")
        abort(404, "File not found")

@routes_bp.route('/download_csv/<filename>', methods=['GET'])
def download_csv(filename):
    """Serve the requested CSV file for download and delete it immediately after."""

    # Sanitize filename to prevent directory traversal attacks
    safe_filename = secure_filename(filename)

    # Define temp directory
    temp_dir = get_user_temp_dir()
    temp_file_path = os.path.join(temp_dir, safe_filename)

    # Normalize path to prevent path traversal
    temp_file_path = os.path.normpath(temp_file_path)

    # Ensure the file is only accessed from the temp directory
    if not temp_file_path.startswith(temp_dir):
        current_app.logger.warning(f"Blocked attempt to access: {filename}")
        abort(400, "Invalid file request")

    if os.path.exists(temp_file_path):
        try:
            response = send_file(temp_file_path, as_attachment=True, download_name=safe_filename, mimetype="text/csv")

            # Delete AFTER the response is fully sent
            @response.call_on_close
            def remove_temp_file():
                try:
                    os.remove(temp_file_path)
                    current_app.logger.info(f"Deleted temporary file: {temp_file_path}")
                except Exception as e:
                    current_app.logger.error(f"Failed to delete file {temp_file_path}: {e}")

            return response
        except Exception as e:
            current_app.logger.error(f"Error serving file {temp_file_path}: {e}")
            abort(500, "Internal server error")
    else:
        current_app.logger.warning(f"File not found: {temp_file_path}")
        abort(404, "File not found")
    
def is_valid_code(code):
    # Ensure the code is alphanumeric and has a reasonable length
    return bool(re.match(r'^[a-zA-Z0-9]{1,20}$', code))  # Adjust length as needed

@routes_bp.route('/enter-code', methods=['GET', 'POST'])
def enter_code():
    ACCESS_CODE = os.getenv('ACCESS_CODE')
    if request.method == 'POST':
        code = request.form.get('code')

        # Validate the input code before comparing
        if not is_valid_code(code):
            return render_template('enter_code.html', error="Invalid access code format.")
        
        if code == ACCESS_CODE:
            session['authenticated'] = True  # Set authenticated status in session
            return redirect(url_for('routes.landing_page'))
        else:
            return render_template('enter_code.html', error="Invalid access code.")
    
    return render_template('enter_code.html')

@routes_bp.route('/download_excel/<filename>', methods=['GET'])
def download_excel(filename):
    """Serve the requested Excel file for download and delete it immediately after."""

    # Sanitize filename to prevent directory traversal attacks
    safe_filename = secure_filename(filename)

    # Define temp directory
    temp_dir = get_user_temp_dir()
    temp_file_path = os.path.join(temp_dir, safe_filename)

    # Normalize path to prevent path traversal
    temp_file_path = os.path.normpath(temp_file_path)

    # Ensure the file is only accessed from the temp directory
    if not temp_file_path.startswith(temp_dir):
        current_app.logger.warning(f"Blocked attempt to access: {filename}")
        abort(400, "Invalid file request")

    if os.path.exists(temp_file_path):
        try:
            response = send_file(temp_file_path, as_attachment=True, download_name=safe_filename, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            # Delete AFTER the response is fully sent
            @response.call_on_close
            def remove_temp_file():
                try:
                    os.remove(temp_file_path)
                    current_app.logger.info(f"Deleted temporary file: {temp_file_path}")
                except Exception as e:
                    current_app.logger.error(f"Failed to delete file {temp_file_path}: {e}")

            return response
        except Exception as e:
            current_app.logger.error(f"Error serving file {temp_file_path}: {e}")
            abort(500, "Internal server error")
    else:
        current_app.logger.warning(f"File not found: {temp_file_path}")
        abort(404, "File not found")

@routes_bp.route('/download_txt/<filename>', methods=['GET'])
def download_txt(filename):
    """Serve the requested text file for download and delete it immediately after."""

    # Sanitize filename to prevent directory traversal attacks
    safe_filename = secure_filename(filename)

    # Define temp directory
    temp_dir = get_user_temp_dir()
    temp_file_path = os.path.join(temp_dir, safe_filename)

    # Normalize path to prevent path traversal
    temp_file_path = os.path.normpath(temp_file_path)

    # Ensure the file is only accessed from the temp directory
    if not temp_file_path.startswith(temp_dir):
        current_app.logger.warning(f"Blocked attempt to access: {filename}")
        abort(400, "Invalid file request")

    if os.path.exists(temp_file_path):
        try:
            response = send_file(temp_file_path, as_attachment=True, download_name="tiktok_urls.txt", mimetype="text/plain")

            # Delete AFTER the response is fully sent
            @response.call_on_close
            def remove_temp_file():
                try:
                    os.remove(temp_file_path)
                    current_app.logger.info(f"Deleted temporary file: {temp_file_path}")
                except Exception as e:
                    current_app.logger.error(f"Failed to delete file {temp_file_path}: {e}")

            return response
        except Exception as e:
            current_app.logger.error(f"Error serving file {temp_file_path}: {e}")
            abort(500, "Internal server error")
    else:
        current_app.logger.warning(f"File not found: {temp_file_path}")
        abort(404, "File not found")