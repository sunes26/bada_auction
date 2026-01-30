# Python 3.9 base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy backend directory
COPY backend/ /app/

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (Railway will override with $PORT)
EXPOSE 8000

# Start command
CMD gunicorn main:app --config gunicorn_conf.py --bind 0.0.0.0:$PORT
