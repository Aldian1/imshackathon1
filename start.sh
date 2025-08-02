#!/bin/bash

# Production start script for Docker deployment

echo "🚀 Starting Browser Use Rappi Agent API"

# Set environment variables (already set in Dockerfile)
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-/ms-playwright}"
export DISABLE_DEV_SHM_USAGE="${DISABLE_DEV_SHM_USAGE:-true}"

# Verify browser installation (browsers should already be installed in Docker image)
echo "🔍 Verifying browser installation..."
playwright --version

# List available browsers
echo "📋 Listing installed browsers..."
ls -la "$PLAYWRIGHT_BROWSERS_PATH" || echo "Using default browser path"

# Quick browser test
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
    # In Docker, log the error but don't exit - let the app start for debugging
    print('⚠️  Continuing with application startup for debugging...')
"

echo "✅ Browser verification completed"

# Start the FastAPI application
echo "🌐 Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}