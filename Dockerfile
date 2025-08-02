# Use Microsoft's official Playwright Python image as base
FROM mcr.microsoft.com/playwright/python:v1.53.0-noble

# Set working directory
WORKDIR /app

# Set environment variables for browser stability
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV DISABLE_DEV_SHM_USAGE=true
ENV HEADLESS=true
ENV BROWSER_USE_HEADLESS=true
ENV DEBIAN_FRONTEND=noninteractive

# Install additional system dependencies for Browser Use
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install playwright browsers (chromium is already included in base image)
RUN playwright install --with-deps

# Copy application code
COPY . .

# Make start script executable
RUN chmod +x start.sh

# The Playwright image already has a proper user setup, just ensure permissions
RUN chmod -R 755 /app /ms-playwright

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use start script as entrypoint
CMD ["./start.sh"]