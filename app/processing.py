from platforms.youtube import process_youtube_file
from platforms.instagram import process_instagram_file
from platforms.tiktok import process_tiktok_file
import tempfile
import logging
import pandas as pd
from flask import render_template  # Needed for rendering templates

logger = logging.getLogger(__name__)

def handle_platform_file_processing(platform, files):
    logger.info("Starting file processing for platform: %s with %d file(s)", platform, len(files))
    try:
        # Initialize all return variables
        df = unique_filename = insights = plot_data = bump_chart_name = heatmap_name = None
        has_valid_data = False

        if platform == 'youtube':
            logger.debug("Processing YouTube files.")
            df, unique_filename, insights, bump_chart_name, heatmap_name, has_valid_data = process_youtube_file(files)
        elif platform == 'instagram':
            logger.debug("Processing Instagram files.")
            df, unique_filename, insights, plot_data, has_valid_data = process_instagram_file(files)
        elif platform == 'tiktok':
            logger.debug("Processing TikTok files.")
            df, unique_filename, insights, plot_data, heatmap_name, has_valid_data = process_tiktok_file(files)
        else:
            logger.error("Invalid platform provided: %s", platform)
            return "Invalid platform", 400

        if not has_valid_data:
            logger.warning("No valid data found for platform: %s", platform)
            return render_template(f'dashboard_{platform}.html', error="No valid data found in the uploaded files.")

        logger.info("Valid data found for platform: %s. Saving CSV to a temporary file.", platform)
        temp_file_path = save_csv_temp_file(df)
        logger.info("Temporary CSV file saved at: %s", temp_file_path)

        logger.info("Rendering dashboard template for platform: %s", platform)
        return render_template(
            f'dashboard_{platform}.html',
            insights=insights,
            data=df.head(5).to_html(classes='data', header="true", index=False),
            plot_data=plot_data,
            bump_chart_data=bump_chart_name,
            heatmap_data=heatmap_name,
            uploaded_files=[file.filename for file in files],
            csv_file_name=temp_file_path
        )

    except Exception as e:
        logger.error("Error processing %s data: %s", platform, e, exc_info=True)
        return render_template(f'dashboard_{platform}.html', error="There was an error processing the data.")

def save_csv_temp_file(df):
    if df.empty:
        logger.error("Attempted to save an empty DataFrame to CSV.")
        raise ValueError("Invalid or empty DataFrame provided.")
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
        df.to_csv(tmp_file.name, index=False)
        logger.info("CSV file created: %s", tmp_file.name)
        return tmp_file.name