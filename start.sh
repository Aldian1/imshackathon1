#!/bin/bash

# Production start script for Sevalla deployment

echo "🚀 Starting Browser Use Rappi Agent API"

# Set environment variables for browser stability
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-/home/app/.cache/ms-playwright}"
export DISABLE_DEV_SHM_USAGE="${DISABLE_DEV_SHM_USAGE:-true}"

# Ensure browsers directory exists
mkdir -p "$PLAYWRIGHT_BROWSERS_PATH"

# Install Playwright browsers in production with detailed logging
echo "📦 Installing Playwright browsers..."
echo "Using browsers path: $PLAYWRIGHT_BROWSERS_PATH"

# Try installation with error handling
if ! playwright install chromium --with-deps --verbose; then
    echo "❌ Failed to install Playwright browsers with deps"
    echo "Attempting installation without deps..."
    if ! playwright install chromium; then
        echo "❌ Failed to install Playwright browsers completely"
        exit 1
    fi
fi

# Verify browser installation
echo "🔍 Verifying browser installation..."
playwright --version

# List installed browsers
echo "📋 Listing installed browsers..."
ls -la "$PLAYWRIGHT_BROWSERS_PATH" || echo "Browser directory not found"

# Test browser launch
echo "🧪 Testing browser launch..."
python3 -c "
import os
import sys
from playwright.sync_api import sync_playwright

try:
    with sync_playwright() as p:
        print('Attempting to launch chromium...')
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox', 
                '--disable-dev-shm-usage',
                '--disable-gpu'
            ]
        )
        print('✅ Browser launch test successful')
        browser.close()
        print('✅ Browser closed successfully')
except Exception as e:
    print(f'❌ Browser launch test failed: {e}')
    print(f'Error type: {type(e).__name__}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Browser test failed - exiting"
    exit 1
fi

echo "✅ Browser installation and test successful"

# Start the FastAPI application
echo "🌐 Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}