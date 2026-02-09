# Python 3.9 base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install minimal system dependencies (Chrome/ChromeDriver removed - using FlareSolverr)
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
COPY backend/requirements.txt /app/requirements.txt

# Install Python dependencies (cached unless requirements.txt changes)
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code (changes frequently)
COPY backend/ /app/

# Create static directory for development fallback
RUN mkdir -p /app/static/thumbnails && chmod -R 777 /app/static || true

# Expose port (Railway will override with $PORT)
EXPOSE 8000

# Start command
CMD gunicorn main:app --config gunicorn_conf.py --bind 0.0.0.0:$PORT
