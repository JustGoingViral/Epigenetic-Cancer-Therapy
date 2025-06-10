"""
Multi-Targeted Epigenetic Cancer Therapy (MTET) Platform
Main FastAPI application entry point

This module initializes the FastAPI application and sets up all routes,
middleware, and core functionality for the MTET platform.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
import os
from typing import Dict, Any

# Import configuration and database
from app.core.config import get_settings
from app.core.security import get_current_user
from app.db.database import engine, get_db

# Import API routers
from app.api.v1 import api_router

# Initialize FastAPI app
app = FastAPI(
    title="MTET Platform API",
    description="Multi-Targeted Epigenetic Cancer Therapy Platform - AI-Enabled Healthcare Solution",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Get settings
settings = get_settings()

# Add security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY
)

# Security scheme
security = HTTPBearer()

# Include API routers
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["root"])
async def root() -> Dict[str, Any]:
    """
    Root endpoint providing basic API information.
    
    Returns:
        Dict containing API status and basic information
    """
    return {
        "message": "MTET Platform API",
        "version": "1.0.0",
        "description": "Multi-Targeted Epigenetic Cancer Therapy Platform",
        "docs_url": "/docs",
        "health_check": "/health"
    }


@app.get("/health", tags=["monitoring"])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
        Dict containing health status and system information
    """
    try:
        # Check database connection
        from sqlalchemy import text
        from app.db.database import SessionLocal
        
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )


@app.get("/api/info", tags=["api"])
async def api_info() -> Dict[str, Any]:
    """
    API information endpoint.
    
    Returns:
        Dict containing detailed API information and available endpoints
    """
    return {
        "api_name": "MTET Platform API",
        "version": "1.0.0",
        "description": "AI-enabled platform for multi-targeted epigenetic cancer therapy",
        "features": [
            "Patient screening and stratification",
            "Biomarker processing and analysis",
            "Clinical decision support",
            "Healthcare system integration",
            "Real-time analytics and reporting"
        ],
        "endpoints": {
            "authentication": "/api/v1/auth",
            "patients": "/api/v1/patients",
            "biomarkers": "/api/v1/biomarkers",
            "analytics": "/api/v1/analytics",
            "integration": "/api/v1/integration"
        },
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json"
        }
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Application startup event handler.
    Initialize necessary services and connections.
    """
    print("🚀 MTET Platform API starting up...")
    print(f"📊 Environment: {settings.ENVIRONMENT}")
    print(f"🔒 Security: {'Enabled' if settings.SECRET_KEY else 'Disabled'}")
    print("✅ Startup completed successfully")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event handler.
    Clean up resources and connections.
    """
    print("🛑 MTET Platform API shutting down...")
    print("✅ Shutdown completed successfully")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False,
        log_level="info"
    )
