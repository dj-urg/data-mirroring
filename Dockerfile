# --- Stage 1: Build dependencies ---
FROM python:3.13-slim AS builder
WORKDIR /app

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies with --use-pep517 flag
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --use-pep517 -r requirements.txt

# --- Stage 2: Final image ---
FROM python:3.13-slim
WORKDIR /app

# Copy installed Python packages from builder stage
COPY --from=builder /root/.local /root/.local
ENV PATH="/root/.local/bin:$PATH"

# Create writable directories with proper permissions
RUN mkdir -p /app/data /tmp/user_uploads && chmod -R 777 /app/data /tmp/user_uploads

# Copy application code
COPY . /app

# Use a non-root user for security
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

# Expose the port your app uses
EXPOSE 5001

# Set environment variables for Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5001
ENV FLASK_ENV=production

# Use Gunicorn for production deployment
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "app:app"]
