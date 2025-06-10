"""
Biomarker management API endpoints for the MTET Platform

This module handles biomarker profiles, analysis, annotations, and compound matching.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
import json

from app.core.security import get_current_active_user, require_clinician, require_researcher
from app.db.database import get_db
from app.db.models import (
    Patient, BiomarkerProfile, BiomarkerAnnotation, 
    Compound, User
)

# Create router
router = APIRouter()


# Pydantic models for request/response
class BiomarkerProfileBase(BaseModel):
    profile_name: str = Field(..., max_length=255)
    sample_type: str = Field(..., max_length=100, description="blood, tissue, saliva, etc.")
    collection_date: datetime


class BiomarkerProfileCreate(BiomarkerProfileBase):
    genetic_mutations: Optional[Dict[str, Any]] = None
    gene_expressions: Optional[Dict[str, Any]] = None
    epigenetic_markers: Optional[Dict[str, Any]] = None
    protein_levels: Optional[Dict[str, Any]] = None


class BiomarkerProfileUpdate(BaseModel):
    profile_name: Optional[str] = Field(None, max_length=255)
    sample_type: Optional[str] = Field(None, max_length=100)
    collection_date: Optional[datetime] = None
    genetic_mutations: Optional[Dict[str, Any]] = None
    gene_expressions: Optional[Dict[str, Any]] = None
    epigenetic_markers: Optional[Dict[str, Any]] = None
    protein_levels: Optional[Dict[str, Any]] = None
    analysis_complete: Optional[bool] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class BiomarkerProfileResponse(BiomarkerProfileBase):
    id: int
    patient_id: int
    genetic_mutations: Optional[Dict[str, Any]]
    gene_expressions: Optional[Dict[str, Any]]
    epigenetic_markers: Optional[Dict[str, Any]]
    protein_levels: Optional[Dict[str, Any]]
    analysis_complete: bool
    analysis_date: Optional[datetime]
    confidence_score: Optional[float]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class BiomarkerAnnotationCreate(BaseModel):
    annotation_type: str = Field(..., max_length=100, description="manual, automated, validated")
    biomarker_name: str = Field(..., max_length=255)
    biomarker_value: Optional[float] = None
    reference_range: Optional[str] = Field(None, max_length=100)
    clinical_significance: Optional[str] = None
    confidence_level: Optional[float] = Field(None, ge=0.0, le=1.0)
    pubmed_refs: Optional[List[str]] = None
    pathway_refs: Optional[List[str]] = None


class BiomarkerAnnotationResponse(BiomarkerAnnotationCreate):
    id: int
    profile_id: int
    annotated_by: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class CompoundResponse(BaseModel):
    id: int
    compound_id: Optional[str]
    name: str
    generic_name: Optional[str]
    brand_names: Optional[List[str]]
    molecular_formula: Optional[str]
    molecular_weight: Optional[float]
    drug_class: Optional[str]
    mechanism_of_action: Optional[str]
    targets: Optional[List[str]]
    pathways: Optional[List[str]]
    fda_approved: bool
    indication: Optional[str]
    
    class Config:
        from_attributes = True


class BiomarkerAnalysisRequest(BaseModel):
    biomarker_data: Dict[str, Any] = Field(..., description="Raw biomarker data for analysis")
    analysis_type: str = Field(..., description="Type of analysis to perform")
    parameters: Optional[Dict[str, Any]] = None


class BiomarkerAnalysisResponse(BaseModel):
    analysis_id: str
    status: str
    results: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    recommendations: Optional[List[str]] = None
    matched_compounds: Optional[List[CompoundResponse]] = None


class CompoundMatchingRequest(BaseModel):
    biomarker_profile_id: int
    matching_criteria: Dict[str, Any] = Field(..., description="Criteria for compound matching")
    include_experimental: bool = Field(default=False, description="Include experimental compounds")


# Helper functions
def get_biomarker_profile_by_id(db: Session, profile_id: int) -> Optional[BiomarkerProfile]:
    """Get biomarker profile by ID."""
    return db.query(BiomarkerProfile).filter(BiomarkerProfile.id == profile_id).first()


def verify_patient_exists(db: Session, patient_id: int) -> bool:
    """Verify that a patient exists."""
    return db.query(Patient).filter(Patient.id == patient_id).first() is not None


# API Endpoints
@router.post("/profiles/{patient_id}", response_model=BiomarkerProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_biomarker_profile(
    patient_id: int,
    profile: BiomarkerProfileCreate,
    current_user: dict = Depends(require_clinician),
    db: Session = Depends(get_db)
):
    """
    Create a new biomarker profile for a patient.
    
    Required role: clinician or admin
    
    - **patient_id**: Patient database ID
    - **profile_name**: Descriptive name for the profile
    - **sample_type**: Type of biological sample (blood, tissue, saliva, etc.)
    - **collection_date**: When the sample was collected
    - **genetic_mutations**: Genetic mutation data (JSON)
    - **gene_expressions**: Gene expression data (JSON)
    - **epigenetic_markers**: Epigenetic marker data (JSON)
    - **protein_levels**: Protein level measurements (JSON)
    """
    # Verify patient exists
    if not verify_patient_exists(db, patient_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Create biomarker profile
    db_profile = BiomarkerProfile(
        patient_id=patient_id,
        profile_name=profile.profile_name,
        sample_type=profile.sample_type,
        collection_date=profile.collection_date,
        genetic_mutations=profile.genetic_mutations,
        gene_expressions=profile.gene_expressions,
        epigenetic_markers=profile.epigenetic_markers,
        protein_levels=profile.protein_levels,
        analysis_complete=False
    )
    
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    
    return db_profile


@router.get("/profiles/{patient_id}", response_model=List[BiomarkerProfileResponse])
async def get_patient_biomarker_profiles(
    patient_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all biomarker profiles for a patient.
    
    - **patient_id**: Patient database ID
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    """
    # Verify patient exists
    if not verify_patient_exists(db, patient_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    profiles = db.query(BiomarkerProfile).filter(
        BiomarkerProfile.patient_id == patient_id
    ).order_by(BiomarkerProfile.collection_date.desc()).offset(skip).limit(limit).all()
    
    return profiles


@router.get("/profiles/detail/{profile_id}", response_model=BiomarkerProfileResponse)
async def get_biomarker_profile(
    profile_id: int,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed biomarker profile information.
    
    - **profile_id**: Biomarker profile ID
    """
    profile = get_biomarker_profile_by_id(db, profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Biomarker profile not found"
        )
    
    return profile


@router.put("/profiles/{profile_id}", response_model=BiomarkerProfileResponse)
async def update_biomarker_profile(
    profile_id: int,
    profile_update: BiomarkerProfileUpdate,
    current_user: dict = Depends(require_clinician),
    db: Session = Depends(get_db)
):
    """
    Update biomarker profile information.
    
    Required role: clinician or admin
    
    - **profile_id**: Biomarker profile ID
    """
    profile = get_biomarker_profile_by_id(db, profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Biomarker profile not found"
        )
    
    # Update profile fields
    update_data = profile_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    # Set analysis date if analysis is marked complete
    if profile_update.analysis_complete and not profile.analysis_date:
        profile.analysis_date = datetime.utcnow()
    
    db.commit()
    db.refresh(profile)
    
    return profile


@router.delete("/profiles/{profile_id}")
async def delete_biomarker_profile(
    profile_id: int,
    current_user: dict = Depends(require_clinician),
    db: Session = Depends(get_db)
):
    """
    Delete a biomarker profile.
    
    Required role: clinician or admin
    Warning: This will delete all associated annotations!
    
    - **profile_id**: Biomarker profile ID
    """
    profile = get_biomarker_profile_by_id(db, profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Biomarker profile not found"
        )
    
    db.delete(profile)
    db.commit()
    
    return {"message": f"Biomarker profile {profile_id} deleted successfully"}


# Annotation endpoints
@router.post("/profiles/{profile_id}/annotations", response_model=BiomarkerAnnotationResponse, status_code=status.HTTP_201_CREATED)
async def create_biomarker_annotation(
    profile_id: int,
    annotation: BiomarkerAnnotationCreate,
    current_user: dict = Depends(require_researcher),
    db: Session = Depends(get_db)
):
    """
    Create a biomarker annotation.
    
    Required role: researcher, clinician, or admin
    
    - **profile_id**: Biomarker profile ID
    - **annotation_type**: Type of annotation (manual, automated, validated)
    - **biomarker_name**: Name of the biomarker
    - **biomarker_value**: Measured value
    - **reference_range**: Normal reference range
    - **clinical_significance**: Clinical interpretation
    - **confidence_level**: Confidence in annotation (0.0 to 1.0)
    - **pubmed_refs**: PubMed reference IDs
    - **pathway_refs**: Pathway database references
    """
    # Verify profile exists
    if not get_biomarker_profile_by_id(db, profile_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Biomarker profile not found"
        )
    
    # Create annotation
    db_annotation = BiomarkerAnnotation(
        profile_id=profile_id,
        annotated_by=current_user["id"],
        annotation_type=annotation.annotation_type,
        biomarker_name=annotation.biomarker_name,
        biomarker_value=annotation.biomarker_value,
        reference_range=annotation.reference_range,
        clinical_significance=annotation.clinical_significance,
        confidence_level=annotation.confidence_level,
        pubmed_refs=annotation.pubmed_refs,
        pathway_refs=annotation.pathway_refs
    )
    
    db.add(db_annotation)
    db.commit()
    db.refresh(db_annotation)
    
    return db_annotation


@router.get("/profiles/{profile_id}/annotations", response_model=List[BiomarkerAnnotationResponse])
async def get_biomarker_annotations(
    profile_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    annotation_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get annotations for a biomarker profile.
    
    - **profile_id**: Biomarker profile ID
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    - **annotation_type**: Filter by annotation type
    """
    # Verify profile exists
    if not get_biomarker_profile_by_id(db, profile_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Biomarker profile not found"
        )
    
    query = db.query(BiomarkerAnnotation).filter(
        BiomarkerAnnotation.profile_id == profile_id
    )
    
    if annotation_type:
        query = query.filter(BiomarkerAnnotation.annotation_type == annotation_type)
    
    annotations = query.order_by(BiomarkerAnnotation.created_at.desc()).offset(skip).limit(limit).all()
    
    return annotations


@router.put("/annotations/{annotation_id}", response_model=BiomarkerAnnotationResponse)
async def update_biomarker_annotation(
    annotation_id: int,
    annotation_update: BiomarkerAnnotationCreate,
    current_user: dict = Depends(require_researcher),
    db: Session = Depends(get_db)
):
    """
    Update a biomarker annotation.
    
    Required role: researcher, clinician, or admin
    
    - **annotation_id**: Annotation ID
    """
    annotation = db.query(BiomarkerAnnotation).filter(
        BiomarkerAnnotation.id == annotation_id
    ).first()
    
    if not annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Annotation not found"
        )
    
    # Update annotation fields
    update_data = annotation_update.dict()
    
    for field, value in update_data.items():
        setattr(annotation, field, value)
    
    db.commit()
    db.refresh(annotation)
    
    return annotation


# Analysis endpoints
@router.post("/analyze", response_model=BiomarkerAnalysisResponse)
async def analyze_biomarker_data(
    analysis_request: BiomarkerAnalysisRequest,
    current_user: dict = Depends(require_researcher),
    db: Session = Depends(get_db)
):
    """
    Analyze biomarker data using AI/ML algorithms.
    
    Required role: researcher, clinician, or admin
    
    - **biomarker_data**: Raw biomarker data for analysis
    - **analysis_type**: Type of analysis (clustering, classification, pathway, etc.)
    - **parameters**: Analysis-specific parameters
    """
    # This is a placeholder for actual AI/ML analysis
    # In a real implementation, this would call machine learning models
    import uuid
    
    analysis_id = str(uuid.uuid4())
    
    # Mock analysis results
    mock_results = {
        "pathway_enrichment": [
            {"pathway": "p53 signaling", "p_value": 0.001, "genes": ["TP53", "MDM2", "CDKN1A"]},
            {"pathway": "DNA repair", "p_value": 0.005, "genes": ["BRCA1", "BRCA2", "ATM"]}
        ],
        "mutation_burden": {
            "total_mutations": 150,
            "high_impact": 12,
            "moderate_impact": 45,
            "low_impact": 93
        },
        "drug_sensitivity_score": 0.75
    }
    
    mock_recommendations = [
        "High TP53 mutation burden suggests platinum-based therapy",
        "BRCA1/2 mutations indicate PARP inhibitor sensitivity",
        "Consider immune checkpoint inhibitors based on mutation load"
    ]
    
    return BiomarkerAnalysisResponse(
        analysis_id=analysis_id,
        status="completed",
        results=mock_results,
        confidence_score=0.85,
        recommendations=mock_recommendations
    )


@router.post("/compound-matching", response_model=List[CompoundResponse])
async def match_compounds(
    matching_request: CompoundMatchingRequest,
    current_user: dict = Depends(require_researcher),
    db: Session = Depends(get_db)
):
    """
    Find compounds that match biomarker profile characteristics.
    
    Required role: researcher, clinician, or admin
    
    - **biomarker_profile_id**: ID of biomarker profile to match against
    - **matching_criteria**: Criteria for compound matching
    - **include_experimental**: Whether to include experimental compounds
    """
    # Verify profile exists
    profile = get_biomarker_profile_by_id(db, matching_request.biomarker_profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Biomarker profile not found"
        )
    
    # Basic compound matching (in real implementation, this would use sophisticated algorithms)
    query = db.query(Compound)
    
    if not matching_request.include_experimental:
        query = query.filter(Compound.fda_approved == True)
    
    # Mock matching based on cancer type (would be much more sophisticated in reality)
    compounds = query.limit(10).all()
    
    return compounds


@router.get("/compounds/search")
async def search_compounds(
    query: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=100),
    fda_approved_only: bool = Query(True),
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Search for compounds by name, mechanism, or target.
    
    - **query**: Search term
    - **limit**: Maximum number of results
    - **fda_approved_only**: Only return FDA-approved compounds
    """
    search_term = f"%{query.lower()}%"
    
    db_query = db.query(Compound).filter(
        or_(
            Compound.name.ilike(search_term),
            Compound.generic_name.ilike(search_term),
            Compound.mechanism_of_action.ilike(search_term),
            Compound.drug_class.ilike(search_term)
        )
    )
    
    if fda_approved_only:
        db_query = db_query.filter(Compound.fda_approved == True)
    
    compounds = db_query.limit(limit).all()
    
    return compounds


@router.post("/upload/{profile_id}")
async def upload_biomarker_data(
    profile_id: int,
    file: UploadFile = File(...),
    data_type: str = Query(..., description="genetic, expression, protein, etc."),
    current_user: dict = Depends(require_clinician),
    db: Session = Depends(get_db)
):
    """
    Upload biomarker data file (CSV, JSON, etc.).
    
    Required role: clinician or admin
    
    - **profile_id**: Biomarker profile ID
    - **file**: Data file to upload
    - **data_type**: Type of data being uploaded
    """
    # Verify profile exists
    profile = get_biomarker_profile_by_id(db, profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Biomarker profile not found"
        )
    
    # Validate file type
    if not file.filename.endswith(('.csv', '.json', '.xlsx', '.txt')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Please upload CSV, JSON, XLSX, or TXT files."
        )
    
    try:
        # Read file content
        content = await file.read()
        
        # Parse based on file type (simplified implementation)
        if file.filename.endswith('.json'):
            data = json.loads(content.decode('utf-8'))
        elif file.filename.endswith('.csv'):
            # In a real implementation, would use pandas or csv module
            data = {"raw_csv_data": content.decode('utf-8')}
        else:
            data = {"raw_data": content.decode('utf-8')}
        
        # Update profile with new data based on type
        if data_type == "genetic":
            profile.genetic_mutations = data
        elif data_type == "expression":
            profile.gene_expressions = data
        elif data_type == "protein":
            profile.protein_levels = data
        elif data_type == "epigenetic":
            profile.epigenetic_markers = data
        
        db.commit()
        db.refresh(profile)
        
        return {
            "message": "File uploaded successfully",
            "filename": file.filename,
            "data_type": data_type,
            "records_processed": len(data) if isinstance(data, dict) else 1
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing file: {str(e)}"
        )


@router.get("/statistics")
async def get_biomarker_statistics(
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get biomarker platform statistics.
    """
    total_profiles = db.query(BiomarkerProfile).count()
    completed_analyses = db.query(BiomarkerProfile).filter(
        BiomarkerProfile.analysis_complete == True
    ).count()
    total_annotations = db.query(BiomarkerAnnotation).count()
    total_compounds = db.query(Compound).count()
    fda_approved_compounds = db.query(Compound).filter(
        Compound.fda_approved == True
    ).count()
    
    return {
        "biomarker_profiles": {
            "total": total_profiles,
            "analyzed": completed_analyses,
            "pending_analysis": total_profiles - completed_analyses
        },
        "annotations": {
            "total": total_annotations
        },
        "compounds": {
            "total": total_compounds,
            "fda_approved": fda_approved_compounds,
            "experimental": total_compounds - fda_approved_compounds
        }
    }
