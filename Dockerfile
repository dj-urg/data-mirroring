# Dockerfile

# Use Python official image from Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy only requirements.txt first to leverage Docker layer caching
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create writable directories and set permissions
RUN mkdir -p /app/data /tmp/user_uploads && chmod -R 777 /app/data /tmp/user_uploads

# Copy the entire project to the container
COPY . /app

# Expose the port that Flask will run on
EXPOSE 5001

# Set environment variables for Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5001
ENV FLASK_ENV=production

# Command to run the application
CMD ["flask", "run"]