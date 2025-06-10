"""
Patient management API endpoints for the MTET Platform

This module handles patient registration, data management, and clinical information.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

from app.core.security import get_current_active_user, require_clinician
from app.db.database import get_db
from app.db.models import Patient, PatientStatus, RiskLevel, ClinicalData

# Create router
router = APIRouter()


# Pydantic models for request/response
class PatientBase(BaseModel):
    patient_id: str = Field(..., description="Unique patient identifier")
    age: Optional[int] = Field(None, ge=0, le=150)
    gender: Optional[str] = Field(None, max_length=10)
    ethnicity: Optional[str] = Field(None, max_length=100)
    primary_diagnosis: Optional[str] = Field(None, max_length=255)
    cancer_type: Optional[str] = Field(None, max_length=100)
    cancer_stage: Optional[str] = Field(None, max_length=20)
    histology: Optional[str] = Field(None, max_length=255)


class PatientCreate(PatientBase):
    previous_treatments: Optional[dict] = None
    enrollment_date: Optional[datetime] = None


class PatientUpdate(BaseModel):
    age: Optional[int] = Field(None, ge=0, le=150)
    gender: Optional[str] = Field(None, max_length=10)
    ethnicity: Optional[str] = Field(None, max_length=100)
    primary_diagnosis: Optional[str] = Field(None, max_length=255)
    cancer_type: Optional[str] = Field(None, max_length=100)
    cancer_stage: Optional[str] = Field(None, max_length=20)
    histology: Optional[str] = Field(None, max_length=255)
    status: Optional[PatientStatus] = None
    previous_treatments: Optional[dict] = None
    risk_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    risk_level: Optional[RiskLevel] = None


class PatientResponse(PatientBase):
    id: int
    status: PatientStatus
    enrollment_date: Optional[datetime]
    last_visit: Optional[datetime]
    risk_score: Optional[float]
    risk_level: Optional[RiskLevel]
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[int]
    
    class Config:
        from_attributes = True


class PatientSummary(BaseModel):
    id: int
    patient_id: str
    age: Optional[int]
    gender: Optional[str]
    cancer_type: Optional[str]
    cancer_stage: Optional[str]
    status: PatientStatus
    risk_level: Optional[RiskLevel]
    last_visit: Optional[datetime]
    
    class Config:
        from_attributes = True


class ClinicalDataCreate(BaseModel):
    visit_date: datetime
    visit_type: str = Field(..., max_length=100)
    weight_kg: Optional[float] = Field(None, gt=0)
    height_cm: Optional[float] = Field(None, gt=0)
    bmi: Optional[float] = Field(None, gt=0)
    blood_pressure_systolic: Optional[int] = Field(None, ge=50, le=300)
    blood_pressure_diastolic: Optional[int] = Field(None, ge=30, le=200)
    lab_values: Optional[dict] = None
    imaging_results: Optional[dict] = None
    clinical_notes: Optional[str] = None


class ClinicalDataResponse(ClinicalDataCreate):
    id: int
    patient_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class PatientSearchFilters(BaseModel):
    cancer_type: Optional[str] = None
    cancer_stage: Optional[str] = None
    status: Optional[PatientStatus] = None
    risk_level: Optional[RiskLevel] = None
    age_min: Optional[int] = Field(None, ge=0)
    age_max: Optional[int] = Field(None, le=150)
    gender: Optional[str] = None
    enrollment_date_start: Optional[datetime] = None
    enrollment_date_end: Optional[datetime] = None


# Helper functions
def get_patient_by_id(db: Session, patient_db_id: int) -> Optional[Patient]:
    """Get patient by database ID."""
    return db.query(Patient).filter(Patient.id == patient_db_id).first()


def get_patient_by_patient_id(db: Session, patient_id: str) -> Optional[Patient]:
    """Get patient by patient ID."""
    return db.query(Patient).filter(Patient.patient_id == patient_id).first()


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """Calculate BMI from weight and height."""
    if not weight_kg or not height_cm or height_cm <= 0:
        return None
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 2)


# API Endpoints
@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient: PatientCreate,
    current_user: dict = Depends(require_clinician),
    db: Session = Depends(get_db)
):
    """
    Create a new patient record.
    
    Required role: clinician or admin
    
    - **patient_id**: Unique patient identifier
    - **age**: Patient age
    - **gender**: Patient gender
    - **ethnicity**: Patient ethnicity
    - **primary_diagnosis**: Primary medical diagnosis
    - **cancer_type**: Type of cancer
    - **cancer_stage**: Cancer staging information
    - **histology**: Histological classification
    - **previous_treatments**: Previous treatment history (JSON)
    - **enrollment_date**: Date of enrollment in study/program
    """
    # Check if patient ID already exists
    if get_patient_by_patient_id(db, patient.patient_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Patient with ID {patient.patient_id} already exists"
        )
    
    # Create new patient
    db_patient = Patient(
        patient_id=patient.patient_id,
        age=patient.age,
        gender=patient.gender,
        ethnicity=patient.ethnicity,
        primary_diagnosis=patient.primary_diagnosis,
        cancer_type=patient.cancer_type,
        cancer_stage=patient.cancer_stage,
        histology=patient.histology,
        previous_treatments=patient.previous_treatments,
        enrollment_date=patient.enrollment_date or datetime.utcnow(),
        status=PatientStatus.ACTIVE,
        created_by=current_user["id"]
    )
    
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    
    return db_patient


@router.get("/", response_model=List[PatientSummary])
async def list_patients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    cancer_type: Optional[str] = Query(None),
    status: Optional[PatientStatus] = Query(None),
    risk_level: Optional[RiskLevel] = Query(None),
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List patients with optional filtering.
    
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    - **cancer_type**: Filter by cancer type
    - **status**: Filter by patient status
    - **risk_level**: Filter by risk level
    """
    query = db.query(Patient)
    
    # Apply filters
    if cancer_type:
        query = query.filter(Patient.cancer_type.ilike(f"%{cancer_type}%"))
    if status:
        query = query.filter(Patient.status == status)
    if risk_level:
        query = query.filter(Patient.risk_level == risk_level)
    
    # Order by most recent first
    query = query.order_by(Patient.created_at.desc())
    
    patients = query.offset(skip).limit(limit).all()
    return patients


@router.get("/search", response_model=List[PatientSummary])
async def search_patients(
    query: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Search patients by patient ID, diagnosis, or cancer type.
    
    - **query**: Search term
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    """
    search_term = f"%{query.lower()}%"
    
    patients = db.query(Patient).filter(
        or_(
            Patient.patient_id.ilike(search_term),
            Patient.primary_diagnosis.ilike(search_term),
            Patient.cancer_type.ilike(search_term),
            Patient.histology.ilike(search_term)
        )
    ).order_by(Patient.created_at.desc()).offset(skip).limit(limit).all()
    
    return patients


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: int,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed patient information by database ID.
    
    - **patient_id**: Patient database ID
    """
    patient = get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    return patient


@router.get("/by-patient-id/{patient_identifier}", response_model=PatientResponse)
async def get_patient_by_identifier(
    patient_identifier: str,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed patient information by patient identifier.
    
    - **patient_identifier**: Patient ID string
    """
    patient = get_patient_by_patient_id(db, patient_identifier)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_identifier} not found"
        )
    
    return patient


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    patient_update: PatientUpdate,
    current_user: dict = Depends(require_clinician),
    db: Session = Depends(get_db)
):
    """
    Update patient information.
    
    Required role: clinician or admin
    
    - **patient_id**: Patient database ID
    """
    patient = get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Update patient fields
    update_data = patient_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(patient, field, value)
    
    # Update last visit if status changes to active
    if patient_update.status and patient_update.status == PatientStatus.ACTIVE:
        patient.last_visit = datetime.utcnow()
    
    db.commit()
    db.refresh(patient)
    
    return patient


@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: int,
    current_user: dict = Depends(require_clinician),
    db: Session = Depends(get_db)
):
    """
    Delete a patient record.
    
    Required role: clinician or admin
    Warning: This will delete all associated data!
    
    - **patient_id**: Patient database ID
    """
    patient = get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    db.delete(patient)
    db.commit()
    
    return {"message": f"Patient {patient.patient_id} deleted successfully"}


# Clinical data endpoints
@router.post("/{patient_id}/clinical-data", response_model=ClinicalDataResponse, status_code=status.HTTP_201_CREATED)
async def add_clinical_data(
    patient_id: int,
    clinical_data: ClinicalDataCreate,
    current_user: dict = Depends(require_clinician),
    db: Session = Depends(get_db)
):
    """
    Add clinical data for a patient.
    
    Required role: clinician or admin
    
    - **patient_id**: Patient database ID
    - **visit_date**: Date of clinical visit
    - **visit_type**: Type of visit (routine, emergency, follow-up, etc.)
    - **weight_kg**: Patient weight in kilograms
    - **height_cm**: Patient height in centimeters
    - **blood_pressure_systolic**: Systolic blood pressure
    - **blood_pressure_diastolic**: Diastolic blood pressure
    - **lab_values**: Laboratory test results (JSON)
    - **imaging_results**: Imaging study results (JSON)
    - **clinical_notes**: Clinical notes and observations
    """
    # Verify patient exists
    patient = get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Calculate BMI if weight and height provided
    bmi = None
    if clinical_data.weight_kg and clinical_data.height_cm:
        bmi = calculate_bmi(clinical_data.weight_kg, clinical_data.height_cm)
    
    # Create clinical data record
    db_clinical_data = ClinicalData(
        patient_id=patient_id,
        visit_date=clinical_data.visit_date,
        visit_type=clinical_data.visit_type,
        weight_kg=clinical_data.weight_kg,
        height_cm=clinical_data.height_cm,
        bmi=bmi,
        blood_pressure_systolic=clinical_data.blood_pressure_systolic,
        blood_pressure_diastolic=clinical_data.blood_pressure_diastolic,
        lab_values=clinical_data.lab_values,
        imaging_results=clinical_data.imaging_results,
        clinical_notes=clinical_data.clinical_notes
    )
    
    db.add(db_clinical_data)
    
    # Update patient's last visit
    patient.last_visit = clinical_data.visit_date
    
    db.commit()
    db.refresh(db_clinical_data)
    
    return db_clinical_data


@router.get("/{patient_id}/clinical-data", response_model=List[ClinicalDataResponse])
async def get_patient_clinical_data(
    patient_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get clinical data for a patient.
    
    - **patient_id**: Patient database ID
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    """
    # Verify patient exists
    patient = get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    clinical_data = db.query(ClinicalData).filter(
        ClinicalData.patient_id == patient_id
    ).order_by(ClinicalData.visit_date.desc()).offset(skip).limit(limit).all()
    
    return clinical_data


# Patient statistics endpoints
@router.get("/{patient_id}/summary")
async def get_patient_summary(
    patient_id: int,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a comprehensive summary of patient data.
    
    - **patient_id**: Patient database ID
    """
    patient = get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Get related data counts
    clinical_data_count = db.query(ClinicalData).filter(
        ClinicalData.patient_id == patient_id
    ).count()
    
    # Get most recent clinical data
    latest_clinical_data = db.query(ClinicalData).filter(
        ClinicalData.patient_id == patient_id
    ).order_by(ClinicalData.visit_date.desc()).first()
    
    return {
        "patient": patient,
        "clinical_visits": clinical_data_count,
        "latest_visit": latest_clinical_data.visit_date if latest_clinical_data else None,
        "latest_clinical_data": latest_clinical_data,
        "biomarker_profiles": 0,  # TODO: Implement biomarker count
        "treatments": 0,  # TODO: Implement treatment count
        "outcomes": 0  # TODO: Implement outcome count
    }


@router.put("/{patient_id}/risk-assessment")
async def update_risk_assessment(
    patient_id: int,
    risk_score: float = Field(..., ge=0.0, le=1.0),
    risk_level: RiskLevel = Field(...),
    current_user: dict = Depends(require_clinician),
    db: Session = Depends(get_db)
):
    """
    Update patient risk assessment.
    
    Required role: clinician or admin
    
    - **patient_id**: Patient database ID
    - **risk_score**: Risk score (0.0 to 1.0)
    - **risk_level**: Risk level category
    """
    patient = get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    patient.risk_score = risk_score
    patient.risk_level = risk_level
    
    db.commit()
    db.refresh(patient)
    
    return {
        "message": "Risk assessment updated successfully",
        "patient_id": patient.patient_id,
        "risk_score": risk_score,
        "risk_level": risk_level
    }
