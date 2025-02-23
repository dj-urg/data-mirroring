# Dockerfile for the Data Mirroring service

# Use Python official image from Docker Hub
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Copy only requirements.txt first to leverage Docker layer caching
COPY requirements.txt /app/

# Install dependencies (as root)
RUN pip install --no-cache-dir -r requirements.txt

# Create writable directories and set secure permissions
RUN mkdir -p /app/data /tmp/user_uploads /app/src && \
    adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app /app/src /tmp/user_uploads && \
    chmod -R 700 /app/src /tmp/user_uploads

# Copy the entire project into the container
COPY . /app

# Expose port 5001 for local development
EXPOSE 5001

# Set environment variables for Flask (default to local port)
ENV FLASK_APP=src/app.py \
    FLASK_RUN_HOST=0.0.0.0 \
    FLASK_RUN_PORT=5001 \
    FLASK_ENV=production

# Use a non-root user for better security
USER appuser

# Command to run the application, using $PORT for Heroku
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "src.app:create_app()"]

# (Optional) Health check to ensure the app is running properly
# Uncomment if curl is installed
# HEALTHCHECK CMD curl --fail http://localhost:5001/ || exit 1