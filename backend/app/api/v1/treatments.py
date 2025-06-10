"""
Treatment management API endpoints for the MTET Platform

This module handles treatment plans, protocols, outcomes, and AI-driven recommendations.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from app.core.security import get_current_active_user, require_clinician, require_researcher
from app.db.database import get_db
from app.db.models import (
    Patient, Treatment, TreatmentStatus, TreatmentOutcome, 
    Compound, BiomarkerProfile
)

# Create router
router = APIRouter()


# Pydantic models for request/response
class TreatmentBase(BaseModel):
    treatment_name: str = Field(..., max_length=255)
    protocol_name: Optional[str] = Field(None, max_length=255)
    treatment_type: str = Field(..., max_length=100, description="single_agent, combination, etc.")
    dosage: Optional[float] = Field(None, gt=0)
    dosage_unit: Optional[str] = Field(None, max_length=50)
    frequency: Optional[str] = Field(None, max_length=100)
    route: Optional[str] = Field(None, max_length=100)


class TreatmentCreate(TreatmentBase):
    compound_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    duration_weeks: Optional[int] = Field(None, gt=0)


class TreatmentUpdate(BaseModel):
    treatment_name: Optional[str] = Field(None, max_length=255)
    protocol_name: Optional[str] = Field(None, max_length=255)
    treatment_type: Optional[str] = Field(None, max_length=100)
    dosage: Optional[float] = Field(None, gt=0)
    dosage_unit: Optional[str] = Field(None, max_length=50)
    frequency: Optional[str] = Field(None, max_length=100)
    route: Optional[str] = Field(None, max_length=100)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    duration_weeks: Optional[int] = Field(None, gt=0)
    status: Optional[TreatmentStatus] = None
    response_assessment: Optional[str] = Field(None, max_length=100)
    toxicity_grade: Optional[int] = Field(None, ge=0, le=5)


class TreatmentResponse(TreatmentBase):
    id: int
    patient_id: int
    compound_id: Optional[int]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    duration_weeks: Optional[int]
    status: TreatmentStatus
    response_assessment: Optional[str]
    toxicity_grade: Optional[int]
    ai_recommended: bool
    recommendation_confidence: Optional[float]
    recommendation_reasoning: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TreatmentSummary(BaseModel):
    id: int
    treatment_name: str
    treatment_type: str
    status: TreatmentStatus
    start_date: Optional[datetime]
    duration_weeks: Optional[int]
    response_assessment: Optional[str]
    ai_recommended: bool
    
    class Config:
        from_attributes = True


class TreatmentOutcomeCreate(BaseModel):
    assessment_date: datetime
    assessment_type: str = Field(..., max_length=100, description="imaging, biomarker, clinical")
    response_category: str = Field(..., max_length=50, description="CR, PR, SD, PD")
    response_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    time_to_response_days: Optional[int] = Field(None, ge=0)
    adverse_events: Optional[Dict[str, Any]] = None
    severity_grade: Optional[int] = Field(None, ge=0, le=5)
    quality_of_life_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    performance_status: Optional[int] = Field(None, ge=0, le=4)
    biomarker_changes: Optional[Dict[str, Any]] = None


class TreatmentOutcomeResponse(TreatmentOutcomeCreate):
    id: int
    patient_id: int
    treatment_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class AIRecommendationRequest(BaseModel):
    patient_id: int
    biomarker_profile_id: Optional[int] = None
    consider_previous_treatments: bool = Field(default=True)
    max_recommendations: int = Field(default=5, ge=1, le=20)
    include_experimental: bool = Field(default=False)


class AIRecommendationResponse(BaseModel):
    recommendation_id: str
    patient_id: int
    recommendations: List[Dict[str, Any]]
    confidence_scores: List[float]
    reasoning: List[str]
    biomarker_considerations: Optional[Dict[str, Any]] = None
    contraindications: Optional[List[str]] = None


# Helper functions
def get_treatment_by_id(db: Session, treatment_id: int) -> Optional[Treatment]:
    """Get treatment by ID."""
    return db.query(Treatment).filter(Treatment.id == treatment_id).first()


def verify_patient_exists(db: Session, patient_id: int) -> bool:
    """Verify that a patient exists."""
    return db.query(Patient).filter(Patient.id == patient_id).first() is not None


def get_patient_treatments(db: Session, patient_id: int, status: Optional[TreatmentStatus] = None) -> List[Treatment]:
    """Get treatments for a patient."""
    query = db.query(Treatment).filter(Treatment.patient_id == patient_id)
    if status:
        query = query.filter(Treatment.status == status)
    return query.order_by(Treatment.start_date.desc()).all()


# API Endpoints
@router.post("/{patient_id}", response_model=TreatmentResponse, status_code=status.HTTP_201_CREATED)
async def create_treatment(
    patient_id: int,
    treatment: TreatmentCreate,
    current_user: dict = Depends(require_clinician),
    db: Session = Depends(get_db)
):
    """
    Create a new treatment plan for a patient.
    
    Required role: clinician or admin
    
    - **patient_id**: Patient database ID
    - **treatment_name**: Name of the treatment
    - **protocol_name**: Clinical protocol name (optional)
    - **treatment_type**: Type (single_agent, combination, etc.)
    - **compound_id**: Associated compound ID (optional)
    - **dosage**: Treatment dosage
    - **dosage_unit**: Unit of dosage (mg, mg/m2, etc.)
    - **frequency**: Dosing frequency
    - **route**: Route of administration
    - **start_date**: Treatment start date
    - **end_date**: Treatment end date (optional)
    - **duration_weeks**: Treatment duration in weeks
    """
    # Verify patient exists
    if not verify_patient_exists(db, patient_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Verify compound exists if provided
    if treatment.compound_id:
        compound = db.query(Compound).filter(Compound.id == treatment.compound_id).first()
        if not compound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Compound not found"
            )
    
    # Create treatment
    db_treatment = Treatment(
        patient_id=patient_id,
        compound_id=treatment.compound_id,
        treatment_name=treatment.treatment_name,
        protocol_name=treatment.protocol_name,
        treatment_type=treatment.treatment_type,
        dosage=treatment.dosage,
        dosage_unit=treatment.dosage_unit,
        frequency=treatment.frequency,
        route=treatment.route,
        start_date=treatment.start_date or datetime.utcnow(),
        end_date=treatment.end_date,
        duration_weeks=treatment.duration_weeks,
        status=TreatmentStatus.PLANNED,
        ai_recommended=False
    )
    
    db.add(db_treatment)
    db.commit()
    db.refresh(db_treatment)
    
    return db_treatment


@router.get("/{patient_id}", response_model=List[TreatmentSummary])
async def get_patient_treatments(
    patient_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    status: Optional[TreatmentStatus] = Query(None),
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all treatments for a patient.
    
    - **patient_id**: Patient database ID
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    - **status**: Filter by treatment status
    """
    # Verify patient exists
    if not verify_patient_exists(db, patient_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    query = db.query(Treatment).filter(Treatment.patient_id == patient_id)
    
    if status:
        query = query.filter(Treatment.status == status)
    
    treatments = query.order_by(Treatment.start_date.desc()).offset(skip).limit(limit).all()
    
    return treatments


@router.get("/detail/{treatment_id}", response_model=TreatmentResponse)
async def get_treatment(
    treatment_id: int,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed treatment information.
    
    - **treatment_id**: Treatment ID
    """
    treatment = get_treatment_by_id(db, treatment_id)
    if not treatment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment not found"
        )
    
    return treatment


@router.put("/{treatment_id}", response_model=TreatmentResponse)
async def update_treatment(
    treatment_id: int,
    treatment_update: TreatmentUpdate,
    current_user: dict = Depends(require_clinician),
    db: Session = Depends(get_db)
):
    """
    Update treatment information.
    
    Required role: clinician or admin
    
    - **treatment_id**: Treatment ID
    """
    treatment = get_treatment_by_id(db, treatment_id)
    if not treatment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment not found"
        )
    
    # Update treatment fields
    update_data = treatment_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(treatment, field, value)
    
    db.commit()
    db.refresh(treatment)
    
    return treatment


@router.delete("/{treatment_id}")
async def delete_treatment(
    treatment_id: int,
    current_user: dict = Depends(require_clinician),
    db: Session = Depends(get_db)
):
    """
    Delete a treatment record.
    
    Required role: clinician or admin
    Warning: This will delete all associated outcomes!
    
    - **treatment_id**: Treatment ID
    """
    treatment = get_treatment_by_id(db, treatment_id)
    if not treatment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment not found"
        )
    
    db.delete(treatment)
    db.commit()
    
    return {"message": f"Treatment {treatment_id} deleted successfully"}


# Treatment outcome endpoints
@router.post("/{treatment_id}/outcomes", response_model=TreatmentOutcomeResponse, status_code=status.HTTP_201_CREATED)
async def create_treatment_outcome(
    treatment_id: int,
    outcome: TreatmentOutcomeCreate,
    current_user: dict = Depends(require_clinician),
    db: Session = Depends(get_db)
):
    """
    Create a treatment outcome assessment.
    
    Required role: clinician or admin
    
    - **treatment_id**: Treatment ID
    - **assessment_date**: Date of assessment
    - **assessment_type**: Type of assessment (imaging, biomarker, clinical)
    - **response_category**: Response category (CR, PR, SD, PD)
    - **response_percentage**: Percentage response (0-100)
    - **time_to_response_days**: Days to achieve response
    - **adverse_events**: Adverse events data (JSON)
    - **severity_grade**: Severity grade (0-5)
    - **quality_of_life_score**: QoL score (0-100)
    - **performance_status**: ECOG performance status (0-4)
    - **biomarker_changes**: Biomarker change data (JSON)
    """
    # Verify treatment exists
    treatment = get_treatment_by_id(db, treatment_id)
    if not treatment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment not found"
        )
    
    # Create outcome
    db_outcome = TreatmentOutcome(
        patient_id=treatment.patient_id,
        treatment_id=treatment_id,
        assessment_date=outcome.assessment_date,
        assessment_type=outcome.assessment_type,
        response_category=outcome.response_category,
        response_percentage=outcome.response_percentage,
        time_to_response_days=outcome.time_to_response_days,
        adverse_events=outcome.adverse_events,
        severity_grade=outcome.severity_grade,
        quality_of_life_score=outcome.quality_of_life_score,
        performance_status=outcome.performance_status,
        biomarker_changes=outcome.biomarker_changes
    )
    
    db.add(db_outcome)
    db.commit()
    db.refresh(db_outcome)
    
    return db_outcome


@router.get("/{treatment_id}/outcomes", response_model=List[TreatmentOutcomeResponse])
async def get_treatment_outcomes(
    treatment_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get outcomes for a treatment.
    
    - **treatment_id**: Treatment ID
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    """
    # Verify treatment exists
    if not get_treatment_by_id(db, treatment_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment not found"
        )
    
    outcomes = db.query(TreatmentOutcome).filter(
        TreatmentOutcome.treatment_id == treatment_id
    ).order_by(TreatmentOutcome.assessment_date.desc()).offset(skip).limit(limit).all()
    
    return outcomes


# AI recommendation endpoints
@router.post("/ai-recommendations", response_model=AIRecommendationResponse)
async def get_ai_treatment_recommendations(
    request: AIRecommendationRequest,
    current_user: dict = Depends(require_clinician),
    db: Session = Depends(get_db)
):
    """
    Get AI-driven treatment recommendations for a patient.
    
    Required role: clinician or admin
    
    - **patient_id**: Patient database ID
    - **biomarker_profile_id**: Biomarker profile to base recommendations on
    - **consider_previous_treatments**: Include previous treatment history
    - **max_recommendations**: Maximum number of recommendations
    - **include_experimental**: Include experimental treatments
    """
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == request.patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Get biomarker profile if specified
    biomarker_profile = None
    if request.biomarker_profile_id:
        biomarker_profile = db.query(BiomarkerProfile).filter(
            BiomarkerProfile.id == request.biomarker_profile_id
        ).first()
        if not biomarker_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Biomarker profile not found"
            )
    
    # Get previous treatments if requested
    previous_treatments = []
    if request.consider_previous_treatments:
        previous_treatments = get_patient_treatments(db, request.patient_id)
    
    # Mock AI recommendations (in real implementation, this would call ML models)
    import uuid
    
    recommendation_id = str(uuid.uuid4())
    
    # Mock recommendations based on patient characteristics
    mock_recommendations = [
        {
            "treatment_name": "Pembrolizumab + Carboplatin",
            "treatment_type": "combination",
            "rationale": "PD-L1 expression and high mutation burden",
            "compound_ids": [1, 2],
            "dosing_schedule": "Pembrolizumab 200mg Q3W + Carboplatin AUC 6",
            "expected_response_rate": 0.65,
            "toxicity_profile": "Grade 3-4 AEs in 30% of patients"
        },
        {
            "treatment_name": "Olaparib",
            "treatment_type": "single_agent",
            "rationale": "BRCA1/2 mutation detected",
            "compound_ids": [3],
            "dosing_schedule": "300mg BID continuous",
            "expected_response_rate": 0.55,
            "toxicity_profile": "Mainly hematologic toxicity"
        },
        {
            "treatment_name": "Docetaxel",
            "treatment_type": "single_agent",
            "rationale": "Standard second-line therapy",
            "compound_ids": [4],
            "dosing_schedule": "75mg/m2 Q3W",
            "expected_response_rate": 0.35,
            "toxicity_profile": "Neutropenia, neuropathy common"
        }
    ]
    
    confidence_scores = [0.85, 0.78, 0.65]
    reasoning = [
        "High PD-L1 expression (80%) and tumor mutation burden (15 mut/Mb) strongly support immunotherapy",
        "Germline BRCA2 mutation with high homologous recombination deficiency score",
        "Progression on first-line therapy, good performance status"
    ]
    
    biomarker_considerations = {
        "pd_l1_expression": 0.80,
        "tumor_mutation_burden": 15.2,
        "brca_status": "BRCA2_mutated",
        "microsatellite_status": "MSS"
    } if biomarker_profile else None
    
    contraindications = [
        "Avoid anti-EGFR therapy due to KRAS mutation",
        "Monitor for pneumonitis with immunotherapy"
    ]
    
    return AIRecommendationResponse(
        recommendation_id=recommendation_id,
        patient_id=request.patient_id,
        recommendations=mock_recommendations[:request.max_recommendations],
        confidence_scores=confidence_scores[:request.max_recommendations],
        reasoning=reasoning[:request.max_recommendations],
        biomarker_considerations=biomarker_considerations,
        contraindications=contraindications
    )


@router.post("/ai-recommendations/{recommendation_id}/implement")
async def implement_ai_recommendation(
    recommendation_id: str,
    recommendation_index: int = Field(..., ge=0),
    patient_id: int = Field(...),
    current_user: dict = Depends(require_clinician),
    db: Session = Depends(get_db)
):
    """
    Implement an AI recommendation as a treatment plan.
    
    Required role: clinician or admin
    
    - **recommendation_id**: AI recommendation ID
    - **recommendation_index**: Index of recommendation to implement
    - **patient_id**: Patient database ID
    """
    # Verify patient exists
    if not verify_patient_exists(db, patient_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # In a real implementation, would retrieve the recommendation from cache/database
    # For now, create a mock treatment based on the request
    
    db_treatment = Treatment(
        patient_id=patient_id,
        treatment_name=f"AI Recommended Treatment #{recommendation_index + 1}",
        protocol_name="AI-Generated Protocol",
        treatment_type="ai_recommended",
        status=TreatmentStatus.PLANNED,
        ai_recommended=True,
        recommendation_confidence=0.85,
        recommendation_reasoning=f"AI recommendation {recommendation_id} index {recommendation_index}"
    )
    
    db.add(db_treatment)
    db.commit()
    db.refresh(db_treatment)
    
    return {
        "message": "AI recommendation implemented successfully",
        "treatment_id": db_treatment.id,
        "recommendation_id": recommendation_id,
        "recommendation_index": recommendation_index
    }


# Treatment analytics endpoints
@router.get("/analytics/response-rates")
async def get_treatment_response_rates(
    cancer_type: Optional[str] = Query(None),
    treatment_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(require_researcher),
    db: Session = Depends(get_db)
):
    """
    Get treatment response rates analytics.
    
    Required role: researcher, clinician, or admin
    
    - **cancer_type**: Filter by cancer type
    - **treatment_type**: Filter by treatment type
    - **limit**: Maximum number of records to analyze
    """
    # This would normally include complex analytics queries
    # Mock response for demonstration
    
    response_data = {
        "overall_response_rate": 0.45,
        "complete_response_rate": 0.15,
        "partial_response_rate": 0.30,
        "stable_disease_rate": 0.25,
        "progressive_disease_rate": 0.30,
        "by_cancer_type": {
            "lung_cancer": {"response_rate": 0.50, "n_patients": 120},
            "breast_cancer": {"response_rate": 0.65, "n_patients": 85},
            "colorectal_cancer": {"response_rate": 0.35, "n_patients": 95}
        },
        "by_treatment_type": {
            "immunotherapy": {"response_rate": 0.55, "n_patients": 150},
            "chemotherapy": {"response_rate": 0.40, "n_patients": 200},
            "targeted_therapy": {"response_rate": 0.60, "n_patients": 100}
        }
    }
    
    return response_data


@router.get("/analytics/toxicity-profiles")
async def get_toxicity_profiles(
    treatment_name: Optional[str] = Query(None),
    severity_grade: Optional[int] = Query(None, ge=1, le=5),
    current_user: dict = Depends(require_researcher),
    db: Session = Depends(get_db)
):
    """
    Get treatment toxicity profiles.
    
    Required role: researcher, clinician, or admin
    
    - **treatment_name**: Filter by treatment name
    - **severity_grade**: Filter by toxicity grade
    """
    # Mock toxicity data
    toxicity_data = {
        "overall_grade_3_4_rate": 0.25,
        "most_common_aes": [
            {"event": "fatigue", "any_grade": 0.65, "grade_3_4": 0.08},
            {"event": "nausea", "any_grade": 0.55, "grade_3_4": 0.05},
            {"event": "neutropenia", "any_grade": 0.45, "grade_3_4": 0.15},
            {"event": "diarrhea", "any_grade": 0.40, "grade_3_4": 0.07}
        ],
        "serious_aes": [
            {"event": "pneumonitis", "incidence": 0.03, "grade_3_4": 0.02},
            {"event": "hepatotoxicity", "incidence": 0.02, "grade_3_4": 0.01}
        ],
        "discontinuation_rate": 0.12
    }
    
    return toxicity_data


@router.get("/statistics")
async def get_treatment_statistics(
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get treatment platform statistics.
    """
    total_treatments = db.query(Treatment).count()
    active_treatments = db.query(Treatment).filter(
        Treatment.status == TreatmentStatus.ACTIVE
    ).count()
    completed_treatments = db.query(Treatment).filter(
        Treatment.status == TreatmentStatus.COMPLETED
    ).count()
    ai_recommended_treatments = db.query(Treatment).filter(
        Treatment.ai_recommended == True
    ).count()
    total_outcomes = db.query(TreatmentOutcome).count()
    
    return {
        "treatments": {
            "total": total_treatments,
            "active": active_treatments,
            "completed": completed_treatments,
            "planned": total_treatments - active_treatments - completed_treatments,
            "ai_recommended": ai_recommended_treatments
        },
        "outcomes": {
            "total": total_outcomes,
            "average_per_treatment": round(total_outcomes / max(total_treatments, 1), 2)
        }
    }
