"""
Configuration management for the MTET Platform

This module handles all application settings, environment variables,
and configuration for different deployment environments.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
import os
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    """
    
    # Application settings
    APP_NAME: str = "MTET Platform API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # Security settings
    SECRET_KEY: str = Field(
        default="your-secret-key-here-change-in-production",
        env="SECRET_KEY"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    ALGORITHM: str = "HS256"
    
    # Database settings
    DATABASE_URL: str = Field(
        default="postgresql://mtet_user:mtet_password@localhost:5432/mtet_db",
        env="DATABASE_URL"
    )
    DATABASE_TEST_URL: str = Field(
        default="postgresql://mtet_user:mtet_password@localhost:5432/mtet_test_db",
        env="DATABASE_TEST_URL"
    )
    
    # Redis settings (for caching and background tasks)
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001"
        ],
        env="ALLOWED_ORIGINS"
    )
    
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1", "*.mtet-platform.com"],
        env="ALLOWED_HOSTS"
    )
    
    # AI/ML Model settings
    MODEL_CACHE_DIR: str = Field(default="./data/models", env="MODEL_CACHE_DIR")
    BIOMARKER_MODEL_PATH: str = Field(
        default="./data/models/biomarker_classifier.pkl",
        env="BIOMARKER_MODEL_PATH"
    )
    PATIENT_STRATIFICATION_MODEL_PATH: str = Field(
        default="./data/models/patient_stratification.pkl",
        env="PATIENT_STRATIFICATION_MODEL_PATH"
    )
    
    # External API settings
    PUBCHEM_API_URL: str = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
    DRUG_BANK_API_URL: str = "https://go.drugbank.com/api/v1"
    CLINICALTRIALS_API_URL: str = "https://clinicaltrials.gov/api"
    
    # Healthcare Integration settings
    FHIR_SERVER_URL: Optional[str] = Field(default=None, env="FHIR_SERVER_URL")
    EHR_INTEGRATION_ENABLED: bool = Field(default=False, env="EHR_INTEGRATION_ENABLED")
    
    # Monitoring and logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    PROMETHEUS_ENABLED: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    
    # File upload settings
    MAX_UPLOAD_SIZE_MB: int = Field(default=100, env="MAX_UPLOAD_SIZE_MB")
    ALLOWED_FILE_TYPES: List[str] = Field(
        default=[".csv", ".xlsx", ".json", ".xml", ".txt"],
        env="ALLOWED_FILE_TYPES"
    )
    
    # Email settings (for notifications)
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USERNAME: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    EMAIL_FROM: str = Field(default="noreply@mtet-platform.com", env="EMAIL_FROM")
    
    # Cloud storage settings
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    AWS_S3_BUCKET: Optional[str] = Field(default=None, env="AWS_S3_BUCKET")
    AWS_REGION: str = Field(default="us-east-1", env="AWS_REGION")
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=100, env="RATE_LIMIT_REQUESTS_PER_MINUTE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    def get_database_url(self) -> str:
        """Get the appropriate database URL based on environment."""
        if self.ENVIRONMENT == "test":
            return self.DATABASE_TEST_URL
        return self.DATABASE_URL
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def is_testing(self) -> bool:
        """Check if running in test environment."""
        return self.ENVIRONMENT.lower() == "test"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings: Application settings instance
    """
    return Settings()


# Environment-specific configurations
class DevelopmentSettings(Settings):
    """Development environment settings."""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    PROMETHEUS_ENABLED: bool = False


class ProductionSettings(Settings):
    """Production environment settings."""
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    PROMETHEUS_ENABLED: bool = True
    
    # More restrictive CORS in production
    ALLOWED_ORIGINS: List[str] = [
        "https://app.mtet-platform.com",
        "https://admin.mtet-platform.com"
    ]


class TestingSettings(Settings):
    """Testing environment settings."""
    ENVIRONMENT: str = "test"
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    DATABASE_URL: str = "sqlite:///./test.db"
    PROMETHEUS_ENABLED: bool = False


def get_environment_settings() -> Settings:
    """
    Get settings based on current environment.
    
    Returns:
        Settings: Environment-specific settings instance
    """
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment == "production":
        return ProductionSettings()
    elif environment == "test":
        return TestingSettings()
    else:
        return DevelopmentSettings()
