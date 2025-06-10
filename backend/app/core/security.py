"""
Security configuration and utilities for HIPAA-compliant healthcare platform.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
import logging

# Security configuration
SECRET_KEY = secrets.token_urlsafe(32)  # Should be from environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security headers for HIPAA compliance
SECURITY_HEADERS = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
}

# Audit logging configuration
audit_logger = logging.getLogger("audit")


class SecurityManager:
    """Central security management for HIPAA compliance."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt."""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def log_access_attempt(user_id: str, resource: str, action: str, success: bool, ip_address: str):
        """Log access attempts for HIPAA audit trail."""
        audit_logger.info(
            f"AUDIT: User={user_id}, Resource={resource}, Action={action}, "
            f"Success={success}, IP={ip_address}, Timestamp={datetime.utcnow().isoformat()}"
        )
    
    @staticmethod
    def encrypt_phi_data(data: str, key: bytes) -> bytes:
        """Encrypt PHI data using AES encryption."""
        from cryptography.fernet import Fernet
        f = Fernet(key)
        return f.encrypt(data.encode())
    
    @staticmethod
    def decrypt_phi_data(encrypted_data: bytes, key: bytes) -> str:
        """Decrypt PHI data."""
        from cryptography.fernet import Fernet
        f = Fernet(key)
        return f.decrypt(encrypted_data).decode()
    
    @staticmethod
    def generate_encryption_key() -> bytes:
        """Generate encryption key for PHI data."""
        from cryptography.fernet import Fernet
        return Fernet.generate_key()
    
    @staticmethod
    def validate_input(data: str, max_length: int = 1000) -> bool:
        """Validate input to prevent injection attacks."""
        if len(data) > max_length:
            return False
        
        # Basic XSS prevention
        dangerous_patterns = ['<script', 'javascript:', 'onload=', 'onerror=']
        data_lower = data.lower()
        for pattern in dangerous_patterns:
            if pattern in data_lower:
                return False
        
        return True
    
    @staticmethod
    def check_rate_limit(user_id: str, endpoint: str, limit: int = 100, window: int = 3600) -> bool:
        """Check rate limiting for API endpoints."""
        # Implementation would use Redis or similar for rate limiting
        # This is a placeholder for the rate limiting logic
        return True
    
    @staticmethod
    def mask_phi_for_logging(data: str) -> str:
        """Mask PHI data for safe logging."""
        # Replace SSN patterns
        import re
        data = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', 'XXX-XX-XXXX', data)
        data = re.sub(r'\b\d{9}\b', 'XXXXXXXXX', data)
        
        # Replace email patterns
        data = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'XXX@XXX.XXX', data)
        
        # Replace phone patterns
        data = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', 'XXX-XXX-XXXX', data)
        data = re.sub(r'\b\(\d{3}\)\s*\d{3}-\d{4}\b', '(XXX) XXX-XXXX', data)
        
        return data


class HIPAACompliance:
    """HIPAA compliance utilities and checks."""
    
    @staticmethod
    def is_phi_field(field_name: str) -> bool:
        """Check if a field contains PHI."""
        phi_fields = [
            'ssn', 'social_security', 'patient_id', 'medical_record_number',
            'phone', 'email', 'address', 'birth_date', 'age', 'diagnosis',
            'treatment', 'medication', 'insurance', 'emergency_contact'
        ]
        return any(phi_field in field_name.lower() for phi_field in phi_fields)
    
    @staticmethod
    def validate_minimum_necessary(user_role: str, requested_data: list) -> list:
        """Implement minimum necessary standard for PHI access."""
        role_permissions = {
            'doctor': ['all'],
            'nurse': ['patient_id', 'diagnosis', 'treatment', 'medication'],
            'admin': ['patient_id', 'insurance', 'contact_info'],
            'researcher': ['anonymized_data_only']
        }
        
        allowed_fields = role_permissions.get(user_role, [])
        if 'all' in allowed_fields:
            return requested_data
        
        return [field for field in requested_data if field in allowed_fields]
    
    @staticmethod
    def log_phi_access(user_id: str, patient_id: str, data_accessed: list, purpose: str):
        """Log PHI access for audit trail."""
        audit_logger.info(
            f"PHI_ACCESS: User={user_id}, Patient={patient_id}, "
            f"Fields={','.join(data_accessed)}, Purpose={purpose}, "
            f"Timestamp={datetime.utcnow().isoformat()}"
        )


# Middleware for security headers
def add_security_headers(response):
    """Add security headers to response."""
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    return response


# Session security
class SessionSecurity:
    """Secure session management."""
    
    @staticmethod
    def generate_session_id() -> str:
        """Generate secure session ID."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def is_session_expired(session_created: datetime, timeout_minutes: int = 30) -> bool:
        """Check if session has expired."""
        expiry_time = session_created + timedelta(minutes=timeout_minutes)
        return datetime.utcnow() > expiry_time
    
    @staticmethod
    def invalidate_session(session_id: str):
        """Invalidate a session."""
        # Implementation would remove session from storage
        pass
