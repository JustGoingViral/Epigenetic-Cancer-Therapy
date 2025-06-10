"""
API v1 package for the MTET Platform

This package contains all v1 API endpoints and routers.
"""

from fastapi import APIRouter
from app.api.v1 import auth, patients, biomarkers, treatments, analytics

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(patients.router, prefix="/patients", tags=["Patients"])
api_router.include_router(biomarkers.router, prefix="/biomarkers", tags=["Biomarkers"])
api_router.include_router(treatments.router, prefix="/treatments", tags=["Treatments"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
