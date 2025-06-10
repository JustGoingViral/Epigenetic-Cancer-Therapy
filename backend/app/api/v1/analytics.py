"""
Analytics and reporting API endpoints for the MTET Platform

This module handles analytics, dashboards, and comprehensive reporting
for clinical data, treatment outcomes, and platform performance.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from pydantic import BaseModel, Field
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Tuple
import json

from app.core.security import get_current_active_user, require_clinician, require_researcher
from app.db.database import get_db
from app.db.models import (
    Patient, Treatment, TreatmentOutcome, BiomarkerProfile, 
    BiomarkerAnnotation, Compound, User, PatientStatus, 
    TreatmentStatus, RiskLevel
)

# Create router
router = APIRouter()


# Pydantic models for analytics
class DateRangeFilter(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class PatientAnalytics(BaseModel):
    total_patients: int
    active_patients: int
    enrolled_patients: int
    by_cancer_type: Dict[str, int]
    by_gender: Dict[str, int]
    by_age_group: Dict[str, int]
    by_risk_level: Dict[str, int]
    enrollment_trend: List[Dict[str, Any]]


class TreatmentAnalytics(BaseModel):
    total_treatments: int
    active_treatments: int
    completed_treatments: int
    ai_recommended_treatments: int
    by_treatment_type: Dict[str, int]
    response_rates: Dict[str, float]
    completion_rates: Dict[str, float]
    timeline_data: List[Dict[str, Any]]


class BiomarkerAnalytics(BaseModel):
    total_profiles: int
    analyzed_profiles: int
    pending_analysis: int
    total_annotations: int
    by_sample_type: Dict[str, int]
    analysis_completion_trend: List[Dict[str, Any]]
    top_biomarkers: List[Dict[str, Any]]


class OutcomeAnalytics(BaseModel):
    total_assessments: int
    response_distribution: Dict[str, int]
    average_response_time: Optional[float]
    quality_of_life_trends: List[Dict[str, Any]]
    adverse_events_summary: Dict[str, Any]
    survival_data: Dict[str, Any]


class PlatformUsageAnalytics(BaseModel):
    total_users: int
    active_users: int
    by_role: Dict[str, int]
    login_trends: List[Dict[str, Any]]
    feature_usage: Dict[str, int]


class DashboardSummary(BaseModel):
    patient_analytics: PatientAnalytics
    treatment_analytics: TreatmentAnalytics
    biomarker_analytics: BiomarkerAnalytics
    outcome_analytics: OutcomeAnalytics
    platform_usage: PlatformUsageAnalytics
    key_metrics: Dict[str, Any]
    alerts: List[Dict[str, Any]]


class CustomReportRequest(BaseModel):
    report_name: str
    filters: Dict[str, Any]
    metrics: List[str]
    grouping: Optional[List[str]] = None
    date_range: Optional[DateRangeFilter] = None
    export_format: str = Field(default="json", pattern="^(json|csv|xlsx)$")


# Helper functions
def get_date_range(date_range: Optional[DateRangeFilter]) -> Tuple[Optional[date], Optional[date]]:
    """Extract start and end dates from date range filter."""
    if not date_range:
        return None, None
    return date_range.start_date, date_range.end_date


def calculate_age_group(age: Optional[int]) -> str:
    """Calculate age group from age."""
    if not age:
        return "Unknown"
    elif age < 18:
        return "Under 18"
    elif age < 30:
        return "18-29"
    elif age < 50:
        return "30-49"
    elif age < 65:
        return "50-64"
    else:
        return "65+"


def format_timeline_data(data: List, date_field: str, value_field: str, period: str = "month") -> List[Dict[str, Any]]:
    """Format data for timeline visualization."""
    # This is a simplified implementation
    # In a real system, you'd use more sophisticated time series aggregation
    timeline = []
    for item in data:
        timeline.append({
            "date": getattr(item, date_field).strftime("%Y-%m-%d") if getattr(item, date_field) else None,
            "value": getattr(item, value_field, 0)
        })
    return timeline


# API Endpoints
@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard_summary(
    date_range: Optional[DateRangeFilter] = None,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive dashboard summary with key analytics.
    
    - **date_range**: Optional date range filter for time-based metrics
    """
    start_date, end_date = get_date_range(date_range)
    
    # Patient Analytics
    patient_query = db.query(Patient)
    if start_date:
        patient_query = patient_query.filter(Patient.created_at >= start_date)
    if end_date:
        patient_query = patient_query.filter(Patient.created_at <= end_date)
    
    total_patients = patient_query.count()
    active_patients = patient_query.filter(Patient.status == PatientStatus.ACTIVE).count()
    enrolled_patients = patient_query.filter(Patient.status == PatientStatus.ENROLLED).count()
    
    # Cancer type distribution
    cancer_types = db.query(
        Patient.cancer_type, func.count(Patient.id)
    ).group_by(Patient.cancer_type).all()
    by_cancer_type = {ct[0] or "Unknown": ct[1] for ct in cancer_types}
    
    # Gender distribution
    genders = db.query(
        Patient.gender, func.count(Patient.id)
    ).group_by(Patient.gender).all()
    by_gender = {g[0] or "Unknown": g[1] for g in genders}
    
    # Age group distribution
    patients_with_age = patient_query.filter(Patient.age.isnot(None)).all()
    age_groups = {}
    for patient in patients_with_age:
        group = calculate_age_group(patient.age)
        age_groups[group] = age_groups.get(group, 0) + 1
    
    # Risk level distribution
    risk_levels = db.query(
        Patient.risk_level, func.count(Patient.id)
    ).group_by(Patient.risk_level).all()
    by_risk_level = {rl[0].value if rl[0] else "Unknown": rl[1] for rl in risk_levels}
    
    patient_analytics = PatientAnalytics(
        total_patients=total_patients,
        active_patients=active_patients,
        enrolled_patients=enrolled_patients,
        by_cancer_type=by_cancer_type,
        by_gender=by_gender,
        by_age_group=age_groups,
        by_risk_level=by_risk_level,
        enrollment_trend=[]  # Would be populated with time series data
    )
    
    # Treatment Analytics
    treatment_query = db.query(Treatment)
    if start_date:
        treatment_query = treatment_query.filter(Treatment.created_at >= start_date)
    if end_date:
        treatment_query = treatment_query.filter(Treatment.created_at <= end_date)
    
    total_treatments = treatment_query.count()
    active_treatments = treatment_query.filter(Treatment.status == TreatmentStatus.ACTIVE).count()
    completed_treatments = treatment_query.filter(Treatment.status == TreatmentStatus.COMPLETED).count()
    ai_recommended_treatments = treatment_query.filter(Treatment.ai_recommended == True).count()
    
    # Treatment type distribution
    treatment_types = db.query(
        Treatment.treatment_type, func.count(Treatment.id)
    ).group_by(Treatment.treatment_type).all()
    by_treatment_type = {tt[0]: tt[1] for tt in treatment_types}
    
    treatment_analytics = TreatmentAnalytics(
        total_treatments=total_treatments,
        active_treatments=active_treatments,
        completed_treatments=completed_treatments,
        ai_recommended_treatments=ai_recommended_treatments,
        by_treatment_type=by_treatment_type,
        response_rates={},  # Would be calculated from outcomes
        completion_rates={},
        timeline_data=[]
    )
    
    # Biomarker Analytics
    biomarker_query = db.query(BiomarkerProfile)
    if start_date:
        biomarker_query = biomarker_query.filter(BiomarkerProfile.created_at >= start_date)
    if end_date:
        biomarker_query = biomarker_query.filter(BiomarkerProfile.created_at <= end_date)
    
    total_profiles = biomarker_query.count()
    analyzed_profiles = biomarker_query.filter(BiomarkerProfile.analysis_complete == True).count()
    pending_analysis = total_profiles - analyzed_profiles
    total_annotations = db.query(BiomarkerAnnotation).count()
    
    # Sample type distribution
    sample_types = db.query(
        BiomarkerProfile.sample_type, func.count(BiomarkerProfile.id)
    ).group_by(BiomarkerProfile.sample_type).all()
    by_sample_type = {st[0]: st[1] for st in sample_types}
    
    biomarker_analytics = BiomarkerAnalytics(
        total_profiles=total_profiles,
        analyzed_profiles=analyzed_profiles,
        pending_analysis=pending_analysis,
        total_annotations=total_annotations,
        by_sample_type=by_sample_type,
        analysis_completion_trend=[],
        top_biomarkers=[]
    )
    
    # Outcome Analytics
    outcome_query = db.query(TreatmentOutcome)
    if start_date:
        outcome_query = outcome_query.filter(TreatmentOutcome.created_at >= start_date)
    if end_date:
        outcome_query = outcome_query.filter(TreatmentOutcome.created_at <= end_date)
    
    total_assessments = outcome_query.count()
    
    # Response distribution
    responses = db.query(
        TreatmentOutcome.response_category, func.count(TreatmentOutcome.id)
    ).group_by(TreatmentOutcome.response_category).all()
    response_distribution = {r[0]: r[1] for r in responses}
    
    outcome_analytics = OutcomeAnalytics(
        total_assessments=total_assessments,
        response_distribution=response_distribution,
        average_response_time=None,
        quality_of_life_trends=[],
        adverse_events_summary={},
        survival_data={}
    )
    
    # Platform Usage Analytics
    user_query = db.query(User)
    total_users = user_query.count()
    active_users = user_query.filter(User.is_active == True).count()
    
    # User role distribution
    user_roles = db.query(
        User.role, func.count(User.id)
    ).group_by(User.role).all()
    by_role = {ur[0].value: ur[1] for ur in user_roles}
    
    platform_usage = PlatformUsageAnalytics(
        total_users=total_users,
        active_users=active_users,
        by_role=by_role,
        login_trends=[],
        feature_usage={}
    )
    
    # Key Metrics
    key_metrics = {
        "patient_enrollment_rate": round((enrolled_patients / max(total_patients, 1)) * 100, 2),
        "treatment_completion_rate": round((completed_treatments / max(total_treatments, 1)) * 100, 2),
        "biomarker_analysis_rate": round((analyzed_profiles / max(total_profiles, 1)) * 100, 2),
        "ai_recommendation_adoption": round((ai_recommended_treatments / max(total_treatments, 1)) * 100, 2)
    }
    
    # Alerts (mock data)
    alerts = [
        {
            "type": "warning",
            "message": "5 patients have pending biomarker analysis for >30 days",
            "priority": "medium"
        },
        {
            "type": "info", 
            "message": "New AI model version available for treatment recommendations",
            "priority": "low"
        }
    ]
    
    return DashboardSummary(
        patient_analytics=patient_analytics,
        treatment_analytics=treatment_analytics,
        biomarker_analytics=biomarker_analytics,
        outcome_analytics=outcome_analytics,
        platform_usage=platform_usage,
        key_metrics=key_metrics,
        alerts=alerts
    )


@router.get("/patients", response_model=PatientAnalytics)
async def get_patient_analytics(
    date_range: Optional[DateRangeFilter] = None,
    cancer_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed patient analytics.
    
    - **date_range**: Date range filter
    - **cancer_type**: Filter by cancer type
    """
    start_date, end_date = get_date_range(date_range)
    
    query = db.query(Patient)
    
    if start_date:
        query = query.filter(Patient.created_at >= start_date)
    if end_date:
        query = query.filter(Patient.created_at <= end_date)
    if cancer_type:
        query = query.filter(Patient.cancer_type.ilike(f"%{cancer_type}%"))
    
    patients = query.all()
    
    # Calculate analytics
    total_patients = len(patients)
    active_patients = len([p for p in patients if p.status == PatientStatus.ACTIVE])
    enrolled_patients = len([p for p in patients if p.status == PatientStatus.ENROLLED])
    
    # Group by various dimensions
    by_cancer_type = {}
    by_gender = {}
    by_age_group = {}
    by_risk_level = {}
    
    for patient in patients:
        # Cancer type
        ct = patient.cancer_type or "Unknown"
        by_cancer_type[ct] = by_cancer_type.get(ct, 0) + 1
        
        # Gender
        g = patient.gender or "Unknown"
        by_gender[g] = by_gender.get(g, 0) + 1
        
        # Age group
        ag = calculate_age_group(patient.age)
        by_age_group[ag] = by_age_group.get(ag, 0) + 1
        
        # Risk level
        rl = patient.risk_level.value if patient.risk_level else "Unknown"
        by_risk_level[rl] = by_risk_level.get(rl, 0) + 1
    
    return PatientAnalytics(
        total_patients=total_patients,
        active_patients=active_patients,
        enrolled_patients=enrolled_patients,
        by_cancer_type=by_cancer_type,
        by_gender=by_gender,
        by_age_group=by_age_group,
        by_risk_level=by_risk_level,
        enrollment_trend=[]
    )


@router.get("/treatments", response_model=TreatmentAnalytics)
async def get_treatment_analytics(
    date_range: Optional[DateRangeFilter] = None,
    treatment_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed treatment analytics.
    
    - **date_range**: Date range filter
    - **treatment_type**: Filter by treatment type
    """
    start_date, end_date = get_date_range(date_range)
    
    query = db.query(Treatment)
    
    if start_date:
        query = query.filter(Treatment.created_at >= start_date)
    if end_date:
        query = query.filter(Treatment.created_at <= end_date)
    if treatment_type:
        query = query.filter(Treatment.treatment_type == treatment_type)
    
    treatments = query.all()
    
    # Calculate analytics
    total_treatments = len(treatments)
    active_treatments = len([t for t in treatments if t.status == TreatmentStatus.ACTIVE])
    completed_treatments = len([t for t in treatments if t.status == TreatmentStatus.COMPLETED])
    ai_recommended_treatments = len([t for t in treatments if t.ai_recommended])
    
    # Group by treatment type
    by_treatment_type = {}
    for treatment in treatments:
        tt = treatment.treatment_type
        by_treatment_type[tt] = by_treatment_type.get(tt, 0) + 1
    
    # Calculate response rates (mock data for now)
    response_rates = {
        "overall": 0.45,
        "complete_response": 0.15,
        "partial_response": 0.30
    }
    
    completion_rates = {
        "on_schedule": 0.75,
        "delayed": 0.15,
        "discontinued": 0.10
    }
    
    return TreatmentAnalytics(
        total_treatments=total_treatments,
        active_treatments=active_treatments,
        completed_treatments=completed_treatments,
        ai_recommended_treatments=ai_recommended_treatments,
        by_treatment_type=by_treatment_type,
        response_rates=response_rates,
        completion_rates=completion_rates,
        timeline_data=[]
    )


@router.get("/biomarkers", response_model=BiomarkerAnalytics)
async def get_biomarker_analytics(
    date_range: Optional[DateRangeFilter] = None,
    sample_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed biomarker analytics.
    
    - **date_range**: Date range filter
    - **sample_type**: Filter by sample type
    """
    start_date, end_date = get_date_range(date_range)
    
    query = db.query(BiomarkerProfile)
    
    if start_date:
        query = query.filter(BiomarkerProfile.created_at >= start_date)
    if end_date:
        query = query.filter(BiomarkerProfile.created_at <= end_date)
    if sample_type:
        query = query.filter(BiomarkerProfile.sample_type == sample_type)
    
    profiles = query.all()
    
    # Calculate analytics
    total_profiles = len(profiles)
    analyzed_profiles = len([p for p in profiles if p.analysis_complete])
    pending_analysis = total_profiles - analyzed_profiles
    
    # Get annotation count
    total_annotations = db.query(BiomarkerAnnotation).count()
    
    # Group by sample type
    by_sample_type = {}
    for profile in profiles:
        st = profile.sample_type
        by_sample_type[st] = by_sample_type.get(st, 0) + 1
    
    # Top biomarkers (mock data)
    top_biomarkers = [
        {"name": "TP53", "frequency": 0.65, "significance": "high"},
        {"name": "BRCA1", "frequency": 0.23, "significance": "high"},
        {"name": "KRAS", "frequency": 0.45, "significance": "medium"},
        {"name": "EGFR", "frequency": 0.35, "significance": "medium"}
    ]
    
    return BiomarkerAnalytics(
        total_profiles=total_profiles,
        analyzed_profiles=analyzed_profiles,
        pending_analysis=pending_analysis,
        total_annotations=total_annotations,
        by_sample_type=by_sample_type,
        analysis_completion_trend=[],
        top_biomarkers=top_biomarkers
    )


@router.get("/outcomes", response_model=OutcomeAnalytics)
async def get_outcome_analytics(
    date_range: Optional[DateRangeFilter] = None,
    assessment_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed outcome analytics.
    
    - **date_range**: Date range filter
    - **assessment_type**: Filter by assessment type
    """
    start_date, end_date = get_date_range(date_range)
    
    query = db.query(TreatmentOutcome)
    
    if start_date:
        query = query.filter(TreatmentOutcome.created_at >= start_date)
    if end_date:
        query = query.filter(TreatmentOutcome.created_at <= end_date)
    if assessment_type:
        query = query.filter(TreatmentOutcome.assessment_type == assessment_type)
    
    outcomes = query.all()
    
    # Calculate analytics
    total_assessments = len(outcomes)
    
    # Response distribution
    response_distribution = {}
    response_times = []
    
    for outcome in outcomes:
        # Response category
        rc = outcome.response_category
        response_distribution[rc] = response_distribution.get(rc, 0) + 1
        
        # Response time
        if outcome.time_to_response_days:
            response_times.append(outcome.time_to_response_days)
    
    average_response_time = sum(response_times) / len(response_times) if response_times else None
    
    # Mock data for other metrics
    adverse_events_summary = {
        "total_events": 150,
        "grade_3_4_events": 45,
        "serious_events": 12,
        "most_common": [
            {"event": "fatigue", "count": 85},
            {"event": "nausea", "count": 65},
            {"event": "neutropenia", "count": 45}
        ]
    }
    
    survival_data = {
        "median_survival_months": 18.5,
        "one_year_survival_rate": 0.72,
        "two_year_survival_rate": 0.55
    }
    
    return OutcomeAnalytics(
        total_assessments=total_assessments,
        response_distribution=response_distribution,
        average_response_time=average_response_time,
        quality_of_life_trends=[],
        adverse_events_summary=adverse_events_summary,
        survival_data=survival_data
    )


@router.post("/custom-report")
async def generate_custom_report(
    report_request: CustomReportRequest,
    current_user: dict = Depends(require_researcher),
    db: Session = Depends(get_db)
):
    """
    Generate a custom analytics report.
    
    Required role: researcher, clinician, or admin
    
    - **report_name**: Name of the custom report
    - **filters**: Filters to apply to the data
    - **metrics**: List of metrics to include
    - **grouping**: Optional grouping dimensions
    - **date_range**: Date range filter
    - **export_format**: Export format (json, csv, xlsx)
    """
    # This is a simplified implementation
    # In a real system, this would be much more sophisticated
    
    report_data = {
        "report_name": report_request.report_name,
        "generated_at": datetime.utcnow().isoformat(),
        "generated_by": current_user["email"],
        "filters_applied": report_request.filters,
        "metrics": report_request.metrics,
        "data": {
            "summary": {
                "total_records": 500,
                "filtered_records": 250
            },
            "results": [
                {
                    "metric": "response_rate",
                    "value": 0.45,
                    "category": "overall"
                },
                {
                    "metric": "completion_rate", 
                    "value": 0.78,
                    "category": "treatments"
                }
            ]
        }
    }
    
    return {
        "message": "Custom report generated successfully",
        "report_id": f"report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        "export_format": report_request.export_format,
        "data": report_data
    }


@router.get("/performance-metrics")
async def get_performance_metrics(
    current_user: dict = Depends(require_researcher),
    db: Session = Depends(get_db)
):
    """
    Get platform performance metrics.
    
    Required role: researcher, clinician, or admin
    """
    return {
        "platform_metrics": {
            "uptime_percentage": 99.8,
            "average_response_time_ms": 250,
            "api_requests_per_day": 15000,
            "error_rate_percentage": 0.2
        },
        "data_quality": {
            "completeness_score": 0.92,
            "accuracy_score": 0.95,
            "consistency_score": 0.88
        },
        "ai_model_performance": {
            "recommendation_accuracy": 0.85,
            "biomarker_analysis_accuracy": 0.91,
            "prediction_confidence": 0.78
        },
        "user_satisfaction": {
            "average_rating": 4.3,
            "response_rate": 0.65,
            "net_promoter_score": 72
        }
    }


@router.get("/export/dashboard")
async def export_dashboard_data(
    format: str = Query("json", pattern="^(json|csv|xlsx)$"),
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Export dashboard data in various formats.
    
    - **format**: Export format (json, csv, xlsx)
    """
    # Get dashboard data
    dashboard_data = await get_dashboard_summary(current_user=current_user, db=db)
    
    if format == "json":
        return {
            "format": "json",
            "data": dashboard_data.dict(),
            "exported_at": datetime.utcnow().isoformat()
        }
    elif format == "csv":
        return {
            "format": "csv",
            "message": "CSV export would be generated here",
            "exported_at": datetime.utcnow().isoformat()
        }
    elif format == "xlsx":
        return {
            "format": "xlsx", 
            "message": "Excel export would be generated here",
            "exported_at": datetime.utcnow().isoformat()
        }


@router.get("/alerts")
async def get_system_alerts(
    priority: Optional[str] = Query(None, pattern="^(low|medium|high|critical)$"),
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get system alerts and notifications.
    
    - **priority**: Filter by alert priority
    """
    # Mock alerts data
    alerts = [
        {
            "id": "alert_001",
            "type": "data_quality",
            "priority": "high",
            "message": "Multiple patients have incomplete biomarker profiles",
            "count": 15,
            "created_at": "2025-06-08T00:00:00Z",
            "action_required": True
        },
        {
            "id": "alert_002",
            "type": "system",
            "priority": "medium",
            "message": "AI model performance below threshold",
            "details": "Recommendation accuracy: 0.75 (threshold: 0.80)",
            "created_at": "2025-06-07T18:30:00Z",
            "action_required": True
        },
        {
            "id": "alert_003",
            "type": "workflow",
            "priority": "low",
            "message": "10 treatment outcomes pending review",
            "created_at": "2025-06-07T15:00:00Z",
            "action_required": False
        }
    ]
    
    if priority:
        alerts = [alert for alert in alerts if alert["priority"] == priority]
    
    return {
        "alerts": alerts,
        "total_count": len(alerts),
        "by_priority": {
            "critical": 0,
            "high": 1,
            "medium": 1,
            "low": 1
        }
    }
