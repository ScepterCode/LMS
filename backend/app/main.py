"""
Main FastAPI application for Learnlyf.
This is the entry point for the backend API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import sys

# Log messages use unicode symbols (checkmarks, warnings) which crash on
# Windows' default cp1252 console/file encoding - force UTF-8 everywhere.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Import application components
from app.core.config import settings, print_config_summary
from app.core.database import initialize_database, cleanup_database, check_database_health
from app.api.v1.api import api_router
from app.middleware.error_handler import setup_exception_handlers


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting Learnlyf Backend...")
    print_config_summary()
    
    # Initialize database connections
    initialize_database()

    # Check database health
    health = check_database_health()
    if not health["overall"]:
        logger.warning("⚠️  No database connection available. Some features may not work.")
        logger.warning("   Please check your SUPABASE configuration.")
    else:
        logger.info("✅ Database connections initialized successfully")
    
    try:
        yield
    finally:
        # Shutdown
        logger.info("🛑 Shutting down Learnlyf Backend...")
        cleanup_database()
        logger.info("✅ Cleanup complete")


# Create FastAPI application
app = FastAPI(
    title="Learnlyf API",
    description="Backend API for Learnlyf - Phase 1 MVP",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Setup exception handlers
setup_exception_handlers(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
        "X-CSRF-Token",
    ],
    expose_headers=["Content-Type", "Authorization"],
    max_age=3600,
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


# ============================================
# ROOT ENDPOINTS
# ============================================

@app.get("/")
def root():
    """
    Root endpoint - API information.
    """
    return {
        "message": "Welcome to Learnlyf API",
        "version": "1.0.0",
        "status": "active",
        "phase": "MVP - Phase 1",
        "docs": "/docs" if settings.DEBUG else None,
        "health": "/health",
        "features": [
            "Authentication",
            "School Registration",
            "System Admin Dashboard",
            "School Admin Dashboard"
        ]
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint for monitoring.
    """
    # Check database health
    db_health = check_database_health()
    
    health_status = {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",  # Will be replaced with actual timestamp
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "database": db_health,
        "services": {
            "authentication": "operational",
            "registration": "operational",
            "api": "operational",
        }
    }
    
    # Determine overall health
    if not db_health["overall"]:
        health_status["status"] = "degraded"
        health_status["database"]["status"] = "unavailable"
    
    return health_status


@app.get("/info")
def system_info():
    """
    System information endpoint.
    """
    import platform
    import psutil
    
    return {
        "system": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
        },
        "application": {
            "name": "Learnlyf",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "host": settings.HOST,
            "port": settings.PORT,
        },
        "database": {
            "available": settings.database_available,
            "supabase_available": settings.supabase_available,
        },
        "security": {
            "jwt_enabled": True,
            "cookie_auth": True,
            "cors_enabled": True,
        }
    }


# ============================================
# DEVELOPMENT ENDPOINTS (Only in debug mode)
# ============================================

if settings.DEBUG:
    
    @app.get("/debug/config")
    def debug_config():
        """
        Debug endpoint to show current configuration.
        Only available in debug mode.
        """
        return {
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "host": settings.HOST,
            "port": settings.PORT,
            "database_available": settings.database_available,
            "supabase_available": settings.supabase_available,
            "cors_origins": settings.get_cors_origins(),
            "jwt_secret_set": bool(settings.JWT_SECRET and settings.JWT_SECRET != "your-super-secret-jwt-key-change-in-production"),
        }
    
    @app.get("/debug/routes")
    def debug_routes():
        """
        Debug endpoint to list all available routes.
        Only available in debug mode.
        """
        routes = []
        for route in app.routes:
            routes.append({
                "path": route.path,
                "name": route.name,
                "methods": list(route.methods) if hasattr(route, "methods") else [],
            })
        
        return {
            "total_routes": len(routes),
            "routes": routes
        }


# ============================================
# ERROR HANDLING EXAMPLE
# ============================================

@app.get("/error-test")
def error_test():
    """
    Test endpoint to demonstrate error handling.
    """
    raise ValueError("This is a test error to demonstrate error handling")


# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting server on http://%s:%d", settings.HOST, settings.PORT)
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )