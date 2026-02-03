# Python 3.9 base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies including Chrome for Selenium (least frequently changed)
RUN apt-get update && apt-get install -y \
    gcc \
    wget \
    gnupg \
    unzip \
    curl \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    libgbm1 \
    libxss1 \
    libxtst6 \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome using modern key management
RUN wget -q -O /tmp/google-chrome-key.pub https://dl-ssl.google.com/linux/linux_signing_key.pub \
    && cat /tmp/google-chrome-key.pub | gpg --dearmor > /etc/apt/trusted.gpg.d/google-chrome.gpg \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/* /tmp/google-chrome-key.pub

# Install ChromeDriver matching Chrome version
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}') && \
    echo "Chrome version: $CHROME_VERSION" && \
    CHROME_MAJOR_VERSION=$(echo $CHROME_VERSION | cut -d'.' -f1) && \
    echo "Chrome major version: $CHROME_MAJOR_VERSION" && \
    if [ "$CHROME_MAJOR_VERSION" -ge 115 ]; then \
        CHROMEDRIVER_URL="https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROME_MAJOR_VERSION}"; \
        CHROMEDRIVER_VERSION=$(curl -s "$CHROMEDRIVER_URL" || echo "$CHROME_VERSION"); \
        echo "ChromeDriver version: $CHROMEDRIVER_VERSION"; \
        wget -q "https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip" -O chromedriver.zip || \
        wget -q "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip" -O chromedriver.zip; \
    else \
        CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR_VERSION}"); \
        echo "ChromeDriver version: $CHROMEDRIVER_VERSION"; \
        wget -q "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" -O chromedriver.zip; \
    fi && \
    unzip chromedriver.zip && \
    if [ -f "chromedriver-linux64/chromedriver" ]; then \
        mv chromedriver-linux64/chromedriver /usr/local/bin/chromedriver; \
    else \
        mv chromedriver /usr/local/bin/chromedriver; \
    fi && \
    chmod +x /usr/local/bin/chromedriver && \
    rm -rf chromedriver.zip chromedriver-linux64 && \
    echo "ChromeDriver installed: $(chromedriver --version)"

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
