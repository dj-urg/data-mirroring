from flask import Blueprint, render_template, request, send_file, current_app, session, redirect, url_for, jsonify
from app.security import requires_authentication
from app.processing import handle_platform_file_processing
from app.extensions import limiter
from platforms.youtube import process_youtube_file
from platforms.instagram import process_instagram_file
from platforms.tiktok import process_tiktok_file
import os
import tempfile
import io
import re


routes_bp = Blueprint('routes', __name__)

@limiter.limit("10 per minute")

@routes_bp.route('/')
@requires_authentication
def landing_page():
    current_app.logger.info("Landing page accessed. IP: %s", request.remote_addr)
    return render_template('homepage.html')

@routes_bp.route('/platform-selection')
@requires_authentication
def platform_selection():
    current_app.logger.info("Platform selection page accessed. IP: %s", request.remote_addr)
    return render_template('platform_selection.html')

@routes_bp.route('/info')
@requires_authentication
def info():
    current_app.logger.info("Info page accessed. IP: %s", request.remote_addr)
    return render_template('info.html')

@routes_bp.route('/data_processing_info')
@requires_authentication
def data_processing_info():
    current_app.logger.info("Data processing info page accessed. IP: %s", request.remote_addr)
    return render_template('data_processing_info.html')

# Handling file processing inside your dashboard route
@routes_bp.route('/dashboard/youtube', methods=['GET', 'POST'])
@requires_authentication
@limiter.limit("10 per minute")
def dashboard_youtube():
    current_app.logger.info("Dashboard accessed for YouTube, Method: %s, IP: %s", request.method, request.remote_addr)
    
    if request.method == 'GET':
        return render_template('dashboard_youtube.html')
    
    files = request.files.getlist('file')
    current_app.logger.info("Processing %d file(s) for YouTube", len(files))
    
    # Call process_youtube_file to get the insights, filenames, and other data
    df, csv_file_name, insights, bump_chart_name, heatmap_name, has_valid_data = process_youtube_file(files)
    
    # Pass all necessary data to the template
    return render_template(
        'dashboard_youtube.html',
        insights=insights,
        csv_file_name=csv_file_name,
        plot_data=bump_chart_name,
        heatmap_data=heatmap_name,
        has_valid_data=has_valid_data
    )

@routes_bp.route('/dashboard/instagram', methods=['GET', 'POST'])
@requires_authentication
@limiter.limit("10 per minute")
def dashboard_instagram():
    current_app.logger.info("Dashboard accessed for Instagram, Method: %s, IP: %s", request.method, request.remote_addr)

    if request.method == 'GET':
        return render_template('dashboard_instagram.html')

    files = request.files.getlist('file')
    current_app.logger.info("Processing %d file(s) for Instagram", len(files))

    df, csv_file_name, insights, bump_chart_name, heatmap_name, csv_preview_html, has_valid_data = process_instagram_file(files)

    return render_template(
        'dashboard_instagram.html',
        insights=insights,
        csv_file_name=csv_file_name,
        plot_data=bump_chart_name,  # Ensure it's used correctly in the HTML
        heatmap_data=heatmap_name,
        has_valid_data=has_valid_data,
        csv_preview_html=csv_preview_html  # Pass the CSV preview string to the template
    )

@routes_bp.route('/dashboard/tiktok', methods=['GET', 'POST'])
@requires_authentication
@limiter.limit("10 per minute")
def dashboard_tiktok():
    current_app.logger.info("Dashboard accessed for TikTok, Method: %s, IP: %s", request.method, request.remote_addr)

    if request.method == 'GET':
        return render_template('dashboard_tiktok.html')

    files = request.files.getlist('file')
    current_app.logger.info("Processing %d file(s) for TikTok", len(files))

    df, csv_file_name, insights, plot_data, heatmap_data, has_valid_data = process_tiktok_file(files)

    return render_template(
        'dashboard_tiktok.html',
        insights=insights,
        csv_file_name=csv_file_name,
        plot_data=plot_data,
        heatmap_data=heatmap_data,
        has_valid_data=has_valid_data
    )
    
@routes_bp.route('/download_image/<filename>', methods=['GET'])
def download_image(filename):
    """Serve the requested image file for download and delete it after sending."""
    temp_file_path = os.path.join(tempfile.gettempdir(), filename)

    if os.path.exists(temp_file_path):
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
    else:
        return "File not found", 404

@routes_bp.route('/download_csv/<filename>', methods=['GET'])
def download_csv(filename):
    """Serve the requested CSV file for download and delete it immediately after."""
    temp_file_path = os.path.join(tempfile.gettempdir(), filename)

    if os.path.exists(temp_file_path):
        response = send_file(temp_file_path, as_attachment=True, download_name=filename, mimetype="text/csv")
        os.remove(temp_file_path)  # Delete file after serving
        return response
    else:
        return "File not found", 404
    
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