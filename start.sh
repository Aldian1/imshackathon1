#!/bin/bash

# Production start script for Sevalla deployment

echo "🚀 Starting Browser Use Rappi Agent API"

# Install Playwright browsers in production
echo "📦 Installing Playwright browsers..."
playwright install chromium --with-deps

# Start the FastAPI application
echo "🌐 Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}