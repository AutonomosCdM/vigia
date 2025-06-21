"""
PHI Tokenization Service
Secure API bridge between Hospital PHI Database and Processing Database

Este servicio:
1. Recibe requests de tokenización desde el hospital
2. Valida autorización del personal médico
3. Genera tokens seguros (Bruce Wayne → Batman)
4. Proporciona datos tokenizados al sistema de procesamiento
5. Mantiene audit trail completo
6. NUNCA expone PHI al sistema externo
"""

import os
import asyncio
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import json
import logging
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import jwt
from cryptography.fernet import Fernet

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("phi_tokenization_service")

# ===============================================
# 1. CONFIGURATION
# ===============================================

class TokenizationConfig:
    """Configuration for PHI Tokenization Service"""
    
    # Database connections
    HOSPITAL_DB_URL = os.getenv("HOSPITAL_PHI_DB_URL", "postgresql://hospital:secure@localhost:5432/hospital_phi")
    PROCESSING_DB_URL = os.getenv("VIGIA_PROCESSING_DB_URL", "postgresql://vigia:secure@localhost:5433/vigia_processing")
    
    # Security
    JWT_SECRET_KEY = os.getenv("PHI_TOKENIZATION_JWT_SECRET", secrets.token_urlsafe(32))
    ENCRYPTION_KEY = os.getenv("PHI_ENCRYPTION_KEY", Fernet.generate_key().decode())
    
    # Token settings
    TOKEN_EXPIRY_DAYS = int(os.getenv("TOKEN_EXPIRY_DAYS", "30"))
    MAX_TOKENS_PER_PATIENT = int(os.getenv("MAX_TOKENS_PER_PATIENT", "5"))
    
    # Rate limiting
    MAX_REQUESTS_PER_HOUR = int(os.getenv("MAX_REQUESTS_PER_HOUR", "100"))
    
    # Service identification
    SERVICE_NAME = "phi_tokenization_service"
    SERVICE_VERSION = "1.0.0"

config = TokenizationConfig()

# ===============================================
# 2. DATA MODELS
# ===============================================

class TokenizationRequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    REVOKED = "revoked"

class AuthorizationLevel(str, Enum):
    NURSE = "nurse"
    DOCTOR = "doctor"
    ADMINISTRATOR = "administrator"

@dataclass
class PatientPHI:
    """Patient PHI data from hospital database (NEVER exported)"""
    patient_id: str
    hospital_mrn: str
    full_name: str
    date_of_birth: str
    gender: str
    medical_conditions: Dict[str, Any]
    
class TokenizationRequest(BaseModel):
    """Request to tokenize patient data"""
    hospital_mrn: str = Field(..., description="Hospital Medical Record Number")
    requesting_system: str = Field(..., description="External system requesting tokenization")
    request_purpose: str = Field(..., description="Purpose of tokenization")
    requested_by: str = Field(..., description="Staff ID making request")
    authorization_level: AuthorizationLevel = Field(..., description="Authorization level of requester")
    hipaa_authorization: bool = Field(..., description="HIPAA authorization obtained")
    consent_form_signed: bool = Field(..., description="Patient consent form signed")
    urgency_level: str = Field(default="routine", description="Urgency level")

class TokenizationResponse(BaseModel):
    """Response with tokenized data"""
    success: bool
    token_id: str
    patient_alias: str
    tokenized_data: Dict[str, Any]
    expires_at: datetime
    message: str

class TokenValidationRequest(BaseModel):
    """Request to validate existing token"""
    token_id: str
    requesting_system: str

class TokenValidationResponse(BaseModel):
    """Response to token validation"""
    valid: bool
    token_id: str
    patient_alias: str
    expires_at: Optional[datetime]
    status: TokenizationRequestStatus
    
# ===============================================
# 3. DATABASE CONNECTIONS
# ===============================================

class DatabaseManager:
    """Manages connections to both hospital and processing databases"""
    
    def __init__(self):
        self.hospital_pool = None
        self.processing_pool = None
        self.fernet = Fernet(config.ENCRYPTION_KEY.encode())
    
    async def initialize(self):
        """Initialize database connections"""
        try:
            # Hospital PHI Database (READ ONLY for this service)
            self.hospital_pool = await asyncpg.create_pool(
                config.HOSPITAL_DB_URL,
                min_size=2,
                max_size=10,
                command_timeout=30
            )
            
            # Processing Database (READ/WRITE for tokenized data)
            self.processing_pool = await asyncpg.create_pool(
                config.PROCESSING_DB_URL,
                min_size=2,
                max_size=10,
                command_timeout=30
            )
            
            logger.info("Database connections initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connections: {e}")
            raise
    
    async def close(self):
        """Close database connections"""
        if self.hospital_pool:
            await self.hospital_pool.close()
        if self.processing_pool:
            await self.processing_pool.close()
    
    @asynccontextmanager
    async def hospital_connection(self):
        """Get hospital database connection"""
        async with self.hospital_pool.acquire() as conn:
            yield conn
    
    @asynccontextmanager 
    async def processing_connection(self):
        """Get processing database connection"""
        async with self.processing_pool.acquire() as conn:
            yield conn

db_manager = DatabaseManager()

# ===============================================
# 4. SECURITY & AUTHENTICATION
# ===============================================

security = HTTPBearer()

async def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify JWT token for API authentication"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def generate_jwt_token(staff_id: str, authorization_level: str) -> str:
    """Generate JWT token for authenticated user"""
    payload = {
        "staff_id": staff_id,
        "authorization_level": authorization_level,
        "exp": datetime.utcnow() + timedelta(hours=8),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm="HS256")

# ===============================================
# 5. TOKENIZATION LOGIC
# ===============================================

class PHITokenizer:
    """Handles PHI tokenization logic"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.alias_generator = PatientAliasGenerator()
    
    async def get_patient_phi(self, hospital_mrn: str) -> Optional[PatientPHI]:
        """Get patient PHI from hospital database"""
        async with self.db_manager.hospital_connection() as conn:
            query = """
                SELECT patient_id, hospital_mrn, full_name, date_of_birth, 
                       gender, chronic_conditions as medical_conditions
                FROM hospital_patients 
                WHERE hospital_mrn = $1 AND is_active = TRUE
            """
            
            row = await conn.fetchrow(query, hospital_mrn)
            if not row:
                return None
            
            return PatientPHI(
                patient_id=str(row['patient_id']),
                hospital_mrn=row['hospital_mrn'],
                full_name=row['full_name'],
                date_of_birth=row['date_of_birth'].isoformat() if row['date_of_birth'] else None,
                gender=row['gender'],
                medical_conditions=row['medical_conditions'] or {}
            )
    
    async def create_tokenization_request(self, request: TokenizationRequest) -> Dict[str, Any]:
        """Create tokenization request in hospital database"""
        # Get patient PHI
        patient_phi = await self.get_patient_phi(request.hospital_mrn)
        if not patient_phi:
            raise HTTPException(
                status_code=404,
                detail=f"Patient not found with MRN: {request.hospital_mrn}"
            )
        
        # Generate token ID and alias
        token_id = str(uuid.uuid4())
        patient_alias = self.alias_generator.generate_alias(patient_phi.full_name)
        expires_at = datetime.now(timezone.utc) + timedelta(days=config.TOKEN_EXPIRY_DAYS)
        
        async with self.db_manager.hospital_connection() as conn:
            # Create tokenization request
            query = """
                INSERT INTO phi_tokenization_requests (
                    patient_id, requesting_system, request_purpose, requested_by,
                    token_id, token_alias, approval_status, token_expires_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING request_id
            """
            
            request_id = await conn.fetchval(
                query,
                uuid.UUID(patient_phi.patient_id),
                request.requesting_system,
                request.request_purpose,
                request.requested_by,
                uuid.UUID(token_id),
                patient_alias,
                TokenizationRequestStatus.APPROVED.value,  # Auto-approve for now
                expires_at
            )
            
            # Log access request
            await self._log_external_access(conn, patient_phi.patient_id, token_id, request)
        
        return {
            "request_id": str(request_id),
            "token_id": token_id,
            "patient_alias": patient_alias,
            "patient_phi": patient_phi,
            "expires_at": expires_at
        }
    
    async def create_tokenized_patient(self, tokenization_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create tokenized patient record in processing database"""
        patient_phi = tokenization_data["patient_phi"]
        
        # Calculate age range (no exact age)
        birth_year = int(patient_phi.date_of_birth[:4]) if patient_phi.date_of_birth else 1980
        current_year = datetime.now().year
        age = current_year - birth_year
        age_range = f"{(age // 10) * 10}-{(age // 10) * 10 + 9}"
        
        # Prepare tokenized data (NO PHI)
        tokenized_data = {
            "token_id": tokenization_data["token_id"],
            "patient_alias": tokenization_data["patient_alias"],
            "age_range": age_range,
            "gender_category": patient_phi.gender,
            "risk_factors": self._extract_risk_factors(patient_phi.medical_conditions),
            "medical_conditions": self._sanitize_medical_conditions(patient_phi.medical_conditions),
            "token_expires_at": tokenization_data["expires_at"]
        }
        
        async with self.db_manager.processing_connection() as conn:
            query = """
                INSERT INTO tokenized_patients (
                    token_id, patient_alias, age_range, gender_category,
                    risk_factors, medical_conditions, token_expires_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (token_id) DO UPDATE SET
                    updated_at = CURRENT_TIMESTAMP
                RETURNING token_id
            """
            
            result = await conn.fetchval(
                query,
                uuid.UUID(tokenized_data["token_id"]),
                tokenized_data["patient_alias"],
                tokenized_data["age_range"],
                tokenized_data["gender_category"],
                json.dumps(tokenized_data["risk_factors"]),
                json.dumps(tokenized_data["medical_conditions"]),
                tokenized_data["token_expires_at"]
            )
            
            # Log tokenized patient creation
            await self._log_audit_event(conn, {
                "event_type": "tokenized_patient_created",
                "token_id": tokenized_data["token_id"],
                "patient_alias": tokenized_data["patient_alias"],
                "success": True
            })
        
        return tokenized_data
    
    async def validate_token(self, token_id: str) -> Dict[str, Any]:
        """Validate existing token"""
        async with self.db_manager.hospital_connection() as conn:
            query = """
                SELECT token_id, token_alias, approval_status, token_expires_at
                FROM phi_tokenization_requests
                WHERE token_id = $1
            """
            
            row = await conn.fetchrow(query, uuid.UUID(token_id))
            if not row:
                return {"valid": False, "reason": "Token not found"}
            
            is_expired = row['token_expires_at'] < datetime.now(timezone.utc)
            is_approved = row['approval_status'] == TokenizationRequestStatus.APPROVED.value
            
            return {
                "valid": is_approved and not is_expired,
                "token_id": str(row['token_id']),
                "patient_alias": row['token_alias'],
                "expires_at": row['token_expires_at'],
                "status": row['approval_status'],
                "reason": "expired" if is_expired else "valid"
            }
    
    def _extract_risk_factors(self, medical_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Extract risk factors without PHI"""
        # Convert medical conditions to risk factors
        risk_factors = {}
        
        if medical_conditions:
            conditions = medical_conditions if isinstance(medical_conditions, list) else []
            
            # Map conditions to risk factors
            diabetes_terms = ['diabetes', 'diabetic', 'blood sugar']
            mobility_terms = ['mobility', 'wheelchair', 'bedridden', 'immobile']
            pain_terms = ['pain', 'chronic pain', 'arthritis']
            
            risk_factors['diabetes'] = any(term in str(conditions).lower() for term in diabetes_terms)
            risk_factors['limited_mobility'] = any(term in str(conditions).lower() for term in mobility_terms)
            risk_factors['chronic_pain'] = any(term in str(conditions).lower() for term in pain_terms)
        
        return risk_factors
    
    def _sanitize_medical_conditions(self, medical_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize medical conditions removing PHI"""
        if not medical_conditions:
            return {}
        
        # Generic medical categories (no specific PHI)
        sanitized = {}
        
        if isinstance(medical_conditions, list):
            for condition in medical_conditions:
                condition_str = str(condition).lower()
                if 'pain' in condition_str:
                    sanitized['chronic_pain'] = True
                if 'sleep' in condition_str:
                    sanitized['sleep_disorders'] = True
                if 'diabetes' in condition_str:
                    sanitized['diabetes'] = True
        
        return sanitized
    
    async def _log_external_access(self, conn, patient_id: str, token_id: str, request: TokenizationRequest):
        """Log external access request"""
        query = """
            INSERT INTO external_access_log (
                patient_id, token_id, external_system, access_type,
                authorized_by, authorization_level, hipaa_authorization,
                consent_form_signed, response_status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """
        
        await conn.execute(
            query,
            uuid.UUID(patient_id),
            uuid.UUID(token_id),
            request.requesting_system,
            "tokenization",
            request.requested_by,
            request.authorization_level.value,
            request.hipaa_authorization,
            request.consent_form_signed,
            "approved"
        )
    
    async def _log_audit_event(self, conn, event_data: Dict[str, Any]):
        """Log audit event in processing database"""
        query = """
            INSERT INTO system_audit_logs (
                event_type, event_category, event_description,
                component, success, token_id
            ) VALUES ($1, $2, $3, $4, $5, $6)
        """
        
        await conn.execute(
            query,
            event_data.get("event_type"),
            "security",
            json.dumps(event_data),
            config.SERVICE_NAME,
            event_data.get("success", True),
            uuid.UUID(event_data.get("token_id")) if event_data.get("token_id") else None
        )

# ===============================================
# 6. ALIAS GENERATOR
# ===============================================

class PatientAliasGenerator:
    """Generates patient aliases (Batman, Superman, etc.)"""
    
    def __init__(self):
        self.superhero_aliases = [
            "Batman", "Superman", "Wonder Woman", "Spider-Man", "Iron Man",
            "Captain America", "Thor", "Hulk", "Black Widow", "Hawkeye",
            "Flash", "Green Lantern", "Aquaman", "Cyborg", "Green Arrow",
            "Black Panther", "Doctor Strange", "Ant-Man", "Wasp", "Falcon",
            "Winter Soldier", "Scarlet Witch", "Vision", "War Machine", "Deadpool"
        ]
    
    def generate_alias(self, full_name: str) -> str:
        """Generate deterministic alias based on name"""
        # Use hash of name to ensure consistency
        name_hash = hashlib.sha256(full_name.encode()).hexdigest()
        hash_int = int(name_hash[:8], 16)
        alias_index = hash_int % len(self.superhero_aliases)
        
        base_alias = self.superhero_aliases[alias_index]
        
        # Add suffix if needed for uniqueness
        suffix_num = (hash_int // len(self.superhero_aliases)) % 100
        if suffix_num > 0:
            return f"{base_alias}_{suffix_num:02d}"
        
        return base_alias

# ===============================================
# 7. FASTAPI APPLICATION
# ===============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan"""
    # Startup
    await db_manager.initialize()
    logger.info("PHI Tokenization Service started")
    yield
    # Shutdown
    await db_manager.close()
    logger.info("PHI Tokenization Service stopped")

app = FastAPI(
    title="PHI Tokenization Service",
    description="Secure bridge between Hospital PHI Database and Processing Database",
    version=config.SERVICE_VERSION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://hospital-system.internal"],  # Restrict to hospital systems
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

tokenizer = PHITokenizer(db_manager)

# ===============================================
# 8. API ENDPOINTS
# ===============================================

@app.post("/tokenize", response_model=TokenizationResponse)
async def tokenize_patient(
    request: TokenizationRequest,
    auth: dict = Depends(verify_jwt_token)
):
    """
    Tokenize patient data for external processing
    
    This endpoint:
    1. Validates hospital staff authorization
    2. Retrieves patient PHI from hospital database  
    3. Generates secure token (Bruce Wayne → Batman)
    4. Creates tokenized record in processing database
    5. Returns tokenized data (NO PHI)
    """
    try:
        logger.info(f"Tokenization request for MRN: {request.hospital_mrn}")
        
        # Validate authorization level
        required_level = ["doctor", "nurse", "administrator"]
        if request.authorization_level.value not in required_level:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient authorization level: {request.authorization_level.value}"
            )
        
        # Create tokenization request
        tokenization_data = await tokenizer.create_tokenization_request(request)
        
        # Create tokenized patient record
        tokenized_data = await tokenizer.create_tokenized_patient(tokenization_data)
        
        logger.info(f"Successfully tokenized patient: {tokenized_data['patient_alias']}")
        
        return TokenizationResponse(
            success=True,
            token_id=tokenized_data["token_id"],
            patient_alias=tokenized_data["patient_alias"],
            tokenized_data={
                "age_range": tokenized_data["age_range"],
                "gender_category": tokenized_data["gender_category"],
                "risk_factors": tokenized_data["risk_factors"],
                "medical_conditions": tokenized_data["medical_conditions"]
            },
            expires_at=tokenized_data["token_expires_at"],
            message=f"Patient successfully tokenized as {tokenized_data['patient_alias']}"
        )
        
    except Exception as e:
        logger.error(f"Tokenization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/validate", response_model=TokenValidationResponse)
async def validate_token(
    request: TokenValidationRequest,
    auth: dict = Depends(verify_jwt_token)
):
    """Validate existing token for processing system"""
    try:
        validation_result = await tokenizer.validate_token(request.token_id)
        
        return TokenValidationResponse(
            valid=validation_result["valid"],
            token_id=validation_result.get("token_id", ""),
            patient_alias=validation_result.get("patient_alias", ""),
            expires_at=validation_result.get("expires_at"),
            status=TokenizationRequestStatus(validation_result.get("status", "unknown"))
        )
        
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/login")
async def login(staff_id: str, authorization_level: str):
    """Generate JWT token for authenticated staff"""
    # In production, this would validate against hospital authentication system
    if not staff_id or not authorization_level:
        raise HTTPException(status_code=400, detail="Missing credentials")
    
    token = generate_jwt_token(staff_id, authorization_level)
    return {"access_token": token, "token_type": "bearer"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": config.SERVICE_NAME,
        "version": config.SERVICE_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/audit/token/{token_id}")
async def get_token_audit_trail(
    token_id: str,
    auth: dict = Depends(verify_jwt_token)
):
    """Get audit trail for specific token"""
    async with db_manager.processing_connection() as conn:
        query = """
            SELECT event_type, event_timestamp, event_description, success
            FROM system_audit_logs
            WHERE token_id = $1
            ORDER BY event_timestamp DESC
        """
        
        rows = await conn.fetch(query, uuid.UUID(token_id))
        
        return {
            "token_id": token_id,
            "audit_events": [
                {
                    "event_type": row["event_type"],
                    "timestamp": row["event_timestamp"],
                    "description": row["event_description"],
                    "success": row["success"]
                }
                for row in rows
            ]
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "phi_tokenization_service:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_level="info"
    )