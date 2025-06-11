"""
Dynamic Patient Questionnaire API for Genetic/Epigenetic Risk Assessment

This module provides endpoints for managing adaptive questionnaires that predict
gene mutations and epigenetic factors based on patient responses.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List, Dict, Any
import json
import math

from app.core.security import get_current_active_user, require_clinician
from app.db.database import get_db
from app.db.models import Patient
from app.services.questionnaire_service import QuestionnaireService
from app.services.risk_calculator import GeneticRiskCalculator

# Create router
router = APIRouter()

# Pydantic models
class QuestionResponse(BaseModel):
    question_id: str = Field(..., description="Unique question identifier")
    response: Any = Field(..., description="Patient's response (string, number, boolean, or list)")
    confidence: Optional[float] = Field(1.0, ge=0.0, le=1.0, description="Response confidence level")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

class QuestionnaireSession(BaseModel):
    session_id: str = Field(..., description="Unique session identifier")
    patient_id: Optional[int] = Field(None, description="Patient database ID")
    questionnaire_type: str = Field(..., description="Type of questionnaire (genetic_screening, epigenetic_assessment)")
    responses: List[QuestionResponse] = Field(default_factory=list)
    current_question_index: int = Field(0)
    is_complete: bool = Field(False)
    risk_scores: Optional[Dict[str, float]] = Field(default_factory=dict)
    recommendations: Optional[List[str]] = Field(default_factory=list)

class QuestionDefinition(BaseModel):
    question_id: str
    question_text: str
    question_type: str  # multiple_choice, boolean, numeric, text, multi_select
    options: Optional[List[str]] = None
    validation_rules: Optional[Dict[str, Any]] = None
    genetic_associations: Optional[Dict[str, float]] = None
    epigenetic_associations: Optional[Dict[str, float]] = None
    category: str  # family_history, symptoms, lifestyle, medical_history
    priority_weight: float = Field(1.0, ge=0.1, le=10.0)
    skip_conditions: Optional[Dict[str, Any]] = None

class RiskPrediction(BaseModel):
    gene_symbol: str
    mutation_probability: float = Field(..., ge=0.0, le=1.0)
    confidence_interval: tuple[float, float]
    evidence_strength: str  # low, moderate, high, very_high
    clinical_significance: str
    recommended_testing: List[str]

class EpigeneticFactor(BaseModel):
    factor_name: str
    risk_level: str  # low, moderate, high
    probability_score: float = Field(..., ge=0.0, le=1.0)
    modifiable: bool
    recommendations: List[str]

class QuestionnaireResult(BaseModel):
    session_id: str
    completion_date: datetime
    total_questions_answered: int
    genetic_predictions: List[RiskPrediction]
    epigenetic_factors: List[EpigeneticFactor]
    overall_risk_score: float
    next_steps: List[str]
    clinical_urgency: str  # routine, elevated, urgent, critical

# Initialize services
questionnaire_service = QuestionnaireService()
risk_calculator = GeneticRiskCalculator()

@router.post("/start-session", response_model=dict)
async def start_questionnaire_session(
    questionnaire_type: str = Field(..., description="genetic_screening or epigenetic_assessment"),
    patient_id: Optional[int] = None,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Start a new questionnaire session.
    
    - **questionnaire_type**: Type of assessment to perform
    - **patient_id**: Optional patient ID to associate with session
    """
    # Validate questionnaire type
    valid_types = ["genetic_screening", "epigenetic_assessment", "comprehensive_assessment"]
    if questionnaire_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid questionnaire type. Must be one of: {valid_types}"
        )
    
    # Verify patient exists if provided
    if patient_id:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
    
    # Create new session
    session = questionnaire_service.create_session(
        questionnaire_type=questionnaire_type,
        patient_id=patient_id,
        created_by=current_user["id"]
    )
    
    # Get first question
    first_question = questionnaire_service.get_next_question(session["session_id"])
    
    return {
        "session_id": session["session_id"],
        "questionnaire_type": questionnaire_type,
        "first_question": first_question,
        "total_estimated_questions": session["estimated_questions"],
        "progress_percentage": 0
    }

@router.get("/questions/{session_id}/next", response_model=dict)
async def get_next_question(
    session_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get the next question in the adaptive questionnaire.
    
    - **session_id**: Unique session identifier
    """
    try:
        question = questionnaire_service.get_next_question(session_id)
        if not question:
            # Session is complete
            result = questionnaire_service.calculate_final_results(session_id)
            return {
                "complete": True,
                "results": result
            }
        
        # Get current progress
        progress = questionnaire_service.get_session_progress(session_id)
        
        return {
            "complete": False,
            "question": question,
            "progress": progress,
            "interim_risks": questionnaire_service.get_interim_risk_scores(session_id)
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.post("/questions/{session_id}/respond")
async def submit_question_response(
    session_id: str,
    response: QuestionResponse,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Submit a response to a question and get the next question.
    
    - **session_id**: Unique session identifier
    - **response**: Patient's response to the current question
    """
    try:
        # Validate and store response
        questionnaire_service.record_response(session_id, response)
        
        # Update risk calculations
        updated_risks = questionnaire_service.update_risk_calculations(session_id)
        
        # Get next question or completion status
        next_question = questionnaire_service.get_next_question(session_id)
        progress = questionnaire_service.get_session_progress(session_id)
        
        if next_question:
            return {
                "success": True,
                "next_question": next_question,
                "progress": progress,
                "updated_risks": updated_risks,
                "complete": False
            }
        else:
            # Questionnaire complete
            final_results = questionnaire_service.calculate_final_results(session_id)
            return {
                "success": True,
                "complete": True,
                "final_results": final_results
            }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/sessions/{session_id}/results", response_model=QuestionnaireResult)
async def get_questionnaire_results(
    session_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get comprehensive results for a completed questionnaire session.
    
    - **session_id**: Unique session identifier
    """
    try:
        results = questionnaire_service.get_session_results(session_id)
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or not completed"
            )
        
        return results
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/sessions/{session_id}/progress")
async def get_session_progress(
    session_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get current progress and interim results for an active session.
    
    - **session_id**: Unique session identifier
    """
    try:
        progress = questionnaire_service.get_session_progress(session_id)
        interim_risks = questionnaire_service.get_interim_risk_scores(session_id)
        
        return {
            "progress": progress,
            "interim_risks": interim_risks,
            "questions_answered": progress["questions_answered"],
            "estimated_remaining": progress["estimated_remaining"]
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.post("/sessions/{session_id}/pause")
async def pause_session(
    session_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Pause a questionnaire session to resume later.
    
    - **session_id**: Unique session identifier
    """
    try:
        result = questionnaire_service.pause_session(session_id)
        return {
            "success": True,
            "message": "Session paused successfully",
            "resume_token": result["resume_token"],
            "expires_at": result["expires_at"]
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.post("/sessions/{session_id}/resume")
async def resume_session(
    session_id: str,
    resume_token: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Resume a paused questionnaire session.
    
    - **session_id**: Unique session identifier
    - **resume_token**: Token provided when session was paused
    """
    try:
        result = questionnaire_service.resume_session(session_id, resume_token)
        next_question = questionnaire_service.get_next_question(session_id)
        progress = questionnaire_service.get_session_progress(session_id)
        
        return {
            "success": True,
            "message": "Session resumed successfully",
            "next_question": next_question,
            "progress": progress,
            "interim_risks": questionnaire_service.get_interim_risk_scores(session_id)
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/questions/bank/{questionnaire_type}")
async def get_question_bank(
    questionnaire_type: str,
    category: Optional[str] = Query(None),
    current_user: dict = Depends(require_clinician)
):
    """
    Get the question bank for a specific questionnaire type.
    
    Required role: clinician or admin
    
    - **questionnaire_type**: Type of questionnaire
    - **category**: Optional category filter
    """
    try:
        questions = questionnaire_service.get_question_bank(questionnaire_type, category)
        return {
            "questionnaire_type": questionnaire_type,
            "category": category,
            "questions": questions,
            "total_questions": len(questions)
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/questions/validate")
async def validate_question_bank(
    current_user: dict = Depends(require_clinician)
):
    """
    Validate the integrity of the question bank and genetic associations.
    
    Required role: clinician or admin
    """
    validation_results = questionnaire_service.validate_question_bank()
    
    return {
        "validation_passed": validation_results["valid"],
        "issues": validation_results.get("issues", []),
        "statistics": validation_results.get("stats", {}),
        "recommendations": validation_results.get("recommendations", [])
    }

@router.get("/analytics/performance")
async def get_questionnaire_analytics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    questionnaire_type: Optional[str] = Query(None),
    current_user: dict = Depends(require_clinician)
):
    """
    Get analytics on questionnaire performance and accuracy.
    
    Required role: clinician or admin
    
    - **start_date**: Start date for analytics period
    - **end_date**: End date for analytics period
    - **questionnaire_type**: Filter by questionnaire type
    """
    analytics = questionnaire_service.get_performance_analytics(
        start_date=start_date,
        end_date=end_date,
        questionnaire_type=questionnaire_type
    )
    
    return analytics

# Patient-facing endpoints (simplified interface)
@router.get("/patient/{patient_id}/recommend-screening")
async def recommend_screening(
    patient_id: int,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Recommend appropriate screening questionnaires for a patient.
    
    - **patient_id**: Patient database ID
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    recommendations = questionnaire_service.recommend_questionnaires(patient)
    
    return {
        "patient_id": patient_id,
        "recommended_questionnaires": recommendations,
        "priority_order": [q["questionnaire_type"] for q in recommendations if q["priority"] == "high"]
    }
