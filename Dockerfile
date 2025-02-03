# Dockerfile

# Use Python official image from Docker Hub
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy only requirements.txt first to leverage Docker layer caching
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create writable directories and set permissions
RUN mkdir -p /app/data /tmp/user_uploads && \
    chmod -R 777 /app/data /tmp/user_uploads

# Copy the entire project into the container
COPY . /app

# Expose the port that Flask will run on
EXPOSE 5001

# Set environment variables for Flask
ENV FLASK_APP=app.py \
    FLASK_RUN_HOST=0.0.0.0 \
    FLASK_RUN_PORT=5001 \
    FLASK_ENV=production

# (Optional) Create a non-root user for improved security
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "app:app"]
