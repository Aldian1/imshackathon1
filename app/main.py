"""
FastAPI main application for Browser Use Rappi Agent
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Import routes
from app.routes.search import router as search_router
from app.models import HealthResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    logger.info("Starting Browser Use Rappi Agent API...")
    
    # Startup
    try:
        # Test browser availability at startup
        logger.info("Testing browser initialization...")
        
        # Import here to avoid circular imports
        from playwright.sync_api import sync_playwright
        
        try:
            with sync_playwright() as p:
                logger.info("Testing chromium launch...")
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu'
                    ]
                )
                logger.info("✅ Chromium launched successfully")
                browser.close()
                logger.info("✅ Browser test completed successfully")
        except Exception as browser_error:
            logger.error(f"❌ Browser test failed: {str(browser_error)}")
            logger.error(f"Error type: {type(browser_error).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            # Don't exit here - let the app start but log the issue
            logger.warning("Browser test failed but continuing with application startup")
        
        logger.info("Application startup complete")
        yield
    finally:
        # Cleanup
        logger.info("Application shutdown")


# Create FastAPI application
app = FastAPI(
    title="Browser Use Rappi Agent",
    description="AI-powered food search agent for rappi.com.ar using Browser Use",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for production deployment
cors_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
cors_origins = [origin.strip() for origin in cors_origins_env.split(",")]

# Add common development and production origins
cors_origins.extend([
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080"
])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search_router, prefix="/api", tags=["search"])


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return HealthResponse(
        status="healthy",
        message="Browser Use Rappi Agent API is running",
        version="1.0.0"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # You could add actual health checks here (database, browser, etc.)
        return HealthResponse(
            status="healthy",
            message="All services are operational",
            version="1.0.0"
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Global exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": "internal_error"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )