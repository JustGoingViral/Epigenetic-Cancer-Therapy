"""
Database models for the MTET Platform

This module defines all SQLAlchemy models for the Multi-Targeted
Epigenetic Cancer Therapy platform, including patients, biomarkers,
treatments, and related entities.
"""

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, 
    String, Text, JSON, Enum, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
import enum

from app.db.database import Base


class TimestampMixin:
    """Mixin for adding timestamp fields to models."""
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class UserRole(str, enum.Enum):
    """User roles in the system."""
    ADMIN = "admin"
    CLINICIAN = "clinician"
    RESEARCHER = "researcher"
    PATIENT = "patient"
    VIEWER = "viewer"


class PatientStatus(str, enum.Enum):
    """Patient status in the system."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ENROLLED = "enrolled"
    COMPLETED = "completed"
    WITHDRAWN = "withdrawn"


class TreatmentStatus(str, enum.Enum):
    """Treatment status."""
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    DISCONTINUED = "discontinued"
    ON_HOLD = "on_hold"


class RiskLevel(str, enum.Enum):
    """Risk assessment levels."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class User(Base, TimestampMixin):
    """User model for authentication and authorization."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    role = Column(Enum(UserRole), default=UserRole.VIEWER)
    last_login = Column(DateTime(timezone=True))
    
    # Professional information
    license_number = Column(String(100))
    institution = Column(String(255))
    department = Column(String(255))
    specialization = Column(String(255))
    
    # Relationships
    created_patients = relationship("Patient", back_populates="created_by_user")
    annotations = relationship("BiomarkerAnnotation", back_populates="annotated_by")


class Patient(Base, TimestampMixin):
    """Patient model for storing patient information."""
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(50), unique=True, index=True, nullable=False)
    
    # Demographics
    age = Column(Integer)
    gender = Column(String(10))
    ethnicity = Column(String(100))
    
    # Medical information
    primary_diagnosis = Column(String(255))
    cancer_type = Column(String(100))
    cancer_stage = Column(String(20))
    histology = Column(String(255))
    previous_treatments = Column(JSON)
    
    # Status and enrollment
    status = Column(Enum(PatientStatus), default=PatientStatus.ACTIVE)
    enrollment_date = Column(DateTime(timezone=True))
    last_visit = Column(DateTime(timezone=True))
    
    # Risk assessment
    risk_score = Column(Float)
    risk_level = Column(Enum(RiskLevel))
    
    # Relationships
    created_by = Column(Integer, ForeignKey("users.id"))
    created_by_user = relationship("User", back_populates="created_patients")
    
    biomarker_profiles = relationship("BiomarkerProfile", back_populates="patient")
    treatments = relationship("Treatment", back_populates="patient")
    clinical_data = relationship("ClinicalData", back_populates="patient")
    outcomes = relationship("TreatmentOutcome", back_populates="patient")

    __table_args__ = (
        Index("ix_patient_cancer_type", "cancer_type"),
        Index("ix_patient_status_created", "status", "created_at"),
    )


class BiomarkerProfile(Base, TimestampMixin):
    """Biomarker profile for patients."""
    __tablename__ = "biomarker_profiles"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    profile_name = Column(String(255))
    sample_type = Column(String(100))  # blood, tissue, saliva, etc.
    collection_date = Column(DateTime(timezone=True))
    
    # Genomic data
    genetic_mutations = Column(JSON)
    gene_expressions = Column(JSON)
    epigenetic_markers = Column(JSON)
    
    # Protein markers
    protein_levels = Column(JSON)
    
    # Analysis results
    analysis_complete = Column(Boolean, default=False)
    analysis_date = Column(DateTime(timezone=True))
    confidence_score = Column(Float)
    
    # Relationships
    patient = relationship("Patient", back_populates="biomarker_profiles")
    annotations = relationship("BiomarkerAnnotation", back_populates="profile")


class BiomarkerAnnotation(Base, TimestampMixin):
    """Annotations and interpretations of biomarker data."""
    __tablename__ = "biomarker_annotations"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("biomarker_profiles.id"), nullable=False)
    annotated_by = Column(Integer, ForeignKey("users.id"))
    
    annotation_type = Column(String(100))  # manual, automated, validated
    biomarker_name = Column(String(255))
    biomarker_value = Column(Float)
    reference_range = Column(String(100))
    clinical_significance = Column(Text)
    confidence_level = Column(Float)
    
    # External references
    pubmed_refs = Column(JSON)
    pathway_refs = Column(JSON)
    
    # Relationships
    profile = relationship("BiomarkerProfile", back_populates="annotations")
    annotated_by_user = relationship("User", back_populates="annotations")


class Compound(Base, TimestampMixin):
    """Therapeutic compounds and drugs."""
    __tablename__ = "compounds"

    id = Column(Integer, primary_key=True, index=True)
    compound_id = Column(String(100), unique=True, index=True)
    name = Column(String(255), nullable=False)
    generic_name = Column(String(255))
    brand_names = Column(JSON)
    
    # Chemical properties
    molecular_formula = Column(String(255))
    molecular_weight = Column(Float)
    smiles = Column(Text)
    inchi = Column(Text)
    
    # Classification
    drug_class = Column(String(255))
    mechanism_of_action = Column(Text)
    targets = Column(JSON)
    pathways = Column(JSON)
    
    # Regulatory information
    fda_approved = Column(Boolean, default=False)
    approval_date = Column(DateTime)
    indication = Column(Text)
    
    # External database IDs
    pubchem_id = Column(String(50))
    drugbank_id = Column(String(50))
    chembl_id = Column(String(50))
    
    # Relationships
    treatments = relationship("Treatment", back_populates="compound")


class Treatment(Base, TimestampMixin):
    """Treatment plans and protocols."""
    __tablename__ = "treatments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    compound_id = Column(Integer, ForeignKey("compounds.id"))
    
    treatment_name = Column(String(255))
    protocol_name = Column(String(255))
    treatment_type = Column(String(100))  # single_agent, combination, etc.
    
    # Dosing information
    dosage = Column(Float)
    dosage_unit = Column(String(50))
    frequency = Column(String(100))
    route = Column(String(100))
    
    # Timeline
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    duration_weeks = Column(Integer)
    
    # Status and monitoring
    status = Column(Enum(TreatmentStatus), default=TreatmentStatus.PLANNED)
    response_assessment = Column(String(100))
    toxicity_grade = Column(Integer)
    
    # AI recommendations
    ai_recommended = Column(Boolean, default=False)
    recommendation_confidence = Column(Float)
    recommendation_reasoning = Column(Text)
    
    # Relationships
    patient = relationship("Patient", back_populates="treatments")
    compound = relationship("Compound", back_populates="treatments")
    outcomes = relationship("TreatmentOutcome", back_populates="treatment")


class TreatmentOutcome(Base, TimestampMixin):
    """Treatment outcomes and response data."""
    __tablename__ = "treatment_outcomes"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    treatment_id = Column(Integer, ForeignKey("treatments.id"))
    
    assessment_date = Column(DateTime(timezone=True))
    assessment_type = Column(String(100))  # imaging, biomarker, clinical
    
    # Response metrics
    response_category = Column(String(50))  # CR, PR, SD, PD
    response_percentage = Column(Float)
    time_to_response_days = Column(Integer)
    
    # Toxicity data
    adverse_events = Column(JSON)
    severity_grade = Column(Integer)
    
    # Quality of life
    quality_of_life_score = Column(Float)
    performance_status = Column(Integer)
    
    # Biomarker changes
    biomarker_changes = Column(JSON)
    
    # Relationships
    patient = relationship("Patient", back_populates="outcomes")
    treatment = relationship("Treatment", back_populates="outcomes")


class ClinicalData(Base, TimestampMixin):
    """Clinical data and measurements."""
    __tablename__ = "clinical_data"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    
    visit_date = Column(DateTime(timezone=True))
    visit_type = Column(String(100))
    
    # Vital signs
    weight_kg = Column(Float)
    height_cm = Column(Float)
    bmi = Column(Float)
    blood_pressure_systolic = Column(Integer)
    blood_pressure_diastolic = Column(Integer)
    
    # Laboratory values
    lab_values = Column(JSON)
    
    # Imaging results
    imaging_results = Column(JSON)
    
    # Clinical notes
    clinical_notes = Column(Text)
    
    # Relationships
    patient = relationship("Patient", back_populates="clinical_data")


class AIModel(Base, TimestampMixin):
    """AI/ML model tracking and metadata."""
    __tablename__ = "ai_models"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(255), nullable=False)
    model_version = Column(String(50))
    model_type = Column(String(100))  # classification, regression, etc.
    
    # Model metadata
    description = Column(Text)
    input_features = Column(JSON)
    output_features = Column(JSON)
    
    # Performance metrics
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    auc_roc = Column(Float)
    
    # Training information
    training_date = Column(DateTime(timezone=True))
    training_samples = Column(Integer)
    validation_samples = Column(Integer)
    
    # Deployment status
    is_active = Column(Boolean, default=False)
    deployment_date = Column(DateTime(timezone=True))
    
    # Model artifacts
    model_path = Column(String(500))
    config_path = Column(String(500))


class AuditLog(Base, TimestampMixin):
    """Audit log for tracking system activities."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(Integer)
    
    # Request details
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    request_method = Column(String(10))
    request_path = Column(String(500))
    
    # Changes made
    old_values = Column(JSON)
    new_values = Column(JSON)
    
    # Additional context
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    __table_args__ = (
        Index("ix_audit_user_action", "user_id", "action"),
        Index("ix_audit_timestamp", "created_at"),
    )


class SystemConfiguration(Base, TimestampMixin):
    """System configuration settings."""
    __tablename__ = "system_configurations"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, nullable=False)
    value = Column(Text)
    data_type = Column(String(50))  # string, integer, float, boolean, json
    description = Column(Text)
    is_sensitive = Column(Boolean, default=False)
    category = Column(String(100))
    
    __table_args__ = (
        Index("ix_config_category", "category"),
    )


# Create indexes for better query performance
Index("ix_patient_risk_level", Patient.risk_level)
Index("ix_biomarker_analysis", BiomarkerProfile.analysis_complete, BiomarkerProfile.analysis_date)
Index("ix_treatment_status_dates", Treatment.status, Treatment.start_date, Treatment.end_date)
Index("ix_outcome_assessment", TreatmentOutcome.assessment_date, TreatmentOutcome.response_category)
