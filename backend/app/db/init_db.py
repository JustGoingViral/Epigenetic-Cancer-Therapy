"""
Database initialization script for the MTET Platform

This script creates the database tables and populates initial data.
"""

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine, create_tables
from app.db.models import (
    Base, User, Patient, Compound, BiomarkerProfile, 
    Treatment, SystemConfiguration, UserRole, PatientStatus, TreatmentStatus
)
from app.core.security import get_password_hash
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """Initialize the database with tables and initial data."""
    logger.info("Creating database tables...")
    
    # Create all tables
    create_tables()
    
    logger.info("Database tables created successfully")


def create_initial_data():
    """Create initial data for the platform."""
    db = SessionLocal()
    
    try:
        # Check if initial data already exists
        if db.query(User).first():
            logger.info("Initial data already exists, skipping...")
            return
        
        logger.info("Creating initial data...")
        
        # Create admin user
        admin_user = User(
            email="admin@mtet-platform.com",
            username="admin",
            hashed_password=get_password_hash("admin123"),
            full_name="System Administrator",
            is_active=True,
            is_verified=True,
            role=UserRole.ADMIN,
            institution="MTET Platform",
            department="Administration",
            specialization="Platform Management"
        )
        db.add(admin_user)
        
        # Create demo clinician
        clinician_user = User(
            email="clinician@mtet-platform.com",
            username="clinician",
            hashed_password=get_password_hash("clinician123"),
            full_name="Dr. Jane Smith",
            is_active=True,
            is_verified=True,
            role=UserRole.CLINICIAN,
            license_number="MD123456",
            institution="City Hospital",
            department="Oncology",
            specialization="Medical Oncology"
        )
        db.add(clinician_user)
        
        # Create demo researcher
        researcher_user = User(
            email="researcher@mtet-platform.com",
            username="researcher",
            hashed_password=get_password_hash("researcher123"),
            full_name="Dr. John Doe",
            is_active=True,
            is_verified=True,
            role=UserRole.RESEARCHER,
            license_number="PhD789012",
            institution="Research Institute",
            department="Cancer Research",
            specialization="Biomarker Analysis"
        )
        db.add(researcher_user)
        
        # Create some sample compounds
        compounds = [
            Compound(
                compound_id="COMP001",
                name="Pembrolizumab",
                generic_name="pembrolizumab",
                brand_names=["Keytruda"],
                molecular_formula="C6538H10110N1712O2036S42",
                molecular_weight=148000.0,
                drug_class="PD-1 inhibitor",
                mechanism_of_action="Blocks PD-1 receptor on T cells",
                targets=["PD-1"],
                pathways=["Immune checkpoint"],
                fda_approved=True,
                approval_date=datetime(2014, 9, 4),
                indication="Various cancer types",
                pubchem_id="57394",
                drugbank_id="DB09037"
            ),
            Compound(
                compound_id="COMP002",
                name="Carboplatin",
                generic_name="carboplatin",
                brand_names=["Paraplatin"],
                molecular_formula="C6H12N2O4Pt",
                molecular_weight=371.25,
                drug_class="Platinum compound",
                mechanism_of_action="DNA cross-linking agent",
                targets=["DNA"],
                pathways=["DNA repair"],
                fda_approved=True,
                approval_date=datetime(1989, 1, 1),
                indication="Ovarian and lung cancer",
                pubchem_id="498142",
                drugbank_id="DB00958"
            ),
            Compound(
                compound_id="COMP003",
                name="Olaparib",
                generic_name="olaparib",
                brand_names=["Lynparza"],
                molecular_formula="C24H23FN4O3",
                molecular_weight=434.46,
                drug_class="PARP inhibitor",
                mechanism_of_action="Inhibits poly ADP ribose polymerase",
                targets=["PARP1", "PARP2"],
                pathways=["DNA repair", "Homologous recombination"],
                fda_approved=True,
                approval_date=datetime(2014, 12, 19),
                indication="BRCA-mutated cancers",
                pubchem_id="23725625",
                drugbank_id="DB09074"
            )
        ]
        
        for compound in compounds:
            db.add(compound)
        
        # Create system configurations
        configs = [
            SystemConfiguration(
                key="platform_version",
                value="1.0.0",
                data_type="string",
                description="Current platform version",
                category="system"
            ),
            SystemConfiguration(
                key="max_file_upload_size",
                value="100",
                data_type="integer",
                description="Maximum file upload size in MB",
                category="uploads"
            ),
            SystemConfiguration(
                key="ai_model_version",
                value="v1.2.3",
                data_type="string",
                description="Current AI model version",
                category="ai"
            ),
            SystemConfiguration(
                key="biomarker_analysis_enabled",
                value="true",
                data_type="boolean",
                description="Enable biomarker analysis features",
                category="features"
            )
        ]
        
        for config in configs:
            db.add(config)
        
        # Commit all changes
        db.commit()
        logger.info("Initial data created successfully")
        
        # Log the created users
        logger.info("Created users:")
        logger.info("  - Admin: admin@mtet-platform.com / admin123")
        logger.info("  - Clinician: clinician@mtet-platform.com / clinician123")
        logger.info("  - Researcher: researcher@mtet-platform.com / researcher123")
        
    except Exception as e:
        logger.error(f"Error creating initial data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def reset_database():
    """Reset the database by dropping and recreating all tables."""
    logger.warning("Resetting database - this will delete all data!")
    
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    logger.info("All tables dropped")
    
    # Recreate tables
    init_database()
    
    # Create initial data
    create_initial_data()
    
    logger.info("Database reset completed")


def main():
    """Main function to initialize the database."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        reset_database()
    else:
        init_database()
        create_initial_data()


if __name__ == "__main__":
    main()
