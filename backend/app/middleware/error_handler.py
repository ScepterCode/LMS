"""
Error handling middleware for Learnlyf.
Provides consistent error responses across the application.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import traceback

from app.core.config import settings
from app.core.exceptions import LearnlyfException, create_error_response

logger = logging.getLogger(__name__)


def setup_exception_handlers(app: FastAPI):
    """
    Setup exception handlers for the FastAPI application.
    """
    
    @app.exception_handler(LearnlyfException)
    async def learnlyf_exception_handler(request: Request, exc: LearnlyfException):
        """Handle custom Learnlyf exceptions."""
        logger.error(
            f"LearnlyfException: {exc.error_code} - {exc.detail}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "error_code": exc.error_code,
            }
        )
        
        error_response = create_error_response(
            exc,
            include_traceback=settings.DEBUG
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions."""
        logger.warning(
            f"HTTPException: {exc.status_code} - {exc.detail}",
            extra={
                "path": request.url.path,
                "method": request.method,
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                    "status_code": exc.status_code,
                }
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors."""
        logger.warning(
            f"ValidationError: {exc.errors()}",
            extra={
                "path": request.url.path,
                "method": request.method,
            }
        )
        
        # Format validation errors
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            })
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "status_code": 422,
                    "details": errors,
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other exceptions."""
        logger.error(
            f"Unhandled exception: {str(exc)}",
            extra={
                "path": request.url.path,
                "method": request.method,
            },
            exc_info=True
        )
        
        # In production, don't expose internal error details
        if settings.is_production:
            message = "An internal server error occurred"
            details = None
        else:
            message = str(exc)
            details = traceback.format_exc()
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": message,
                    "status_code": 500,
                    "traceback": details if settings.DEBUG else None,
                }
            }
        )
    
    logger.info("Exception handlers configured")