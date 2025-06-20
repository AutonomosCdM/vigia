"""
OAuth 2.0 and Multi-Factor Authentication Manager for Vigia Medical AI
HIPAA-compliant authentication with medical-grade security
"""

import os
import secrets
import hashlib
import qrcode
import base64
import hmac
import time
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json

try:
    import jwt
    HAS_JWT = True
except ImportError:
    HAS_JWT = False

try:
    import pyotp
    HAS_PYOTP = True
except ImportError:
    HAS_PYOTP = False

try:
    from passlib.context import CryptContext
    HAS_PASSLIB = True
except ImportError:
    HAS_PASSLIB = False

from .secrets_manager import get_secret
from .audit_service import AuditService, AuditEventType, AuditLevel

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """User roles with medical hierarchy"""
    PATIENT = "patient"                    # Patient access (limited)
    NURSE = "nurse"                       # Nursing staff
    PHYSICIAN = "physician"               # Medical doctor
    SPECIALIST = "specialist"             # Medical specialist
    ADMIN = "admin"                       # System administrator
    SUPER_ADMIN = "super_admin"           # Super administrator
    EMERGENCY = "emergency"               # Emergency access
    AUDIT = "audit"                       # Audit-only access


class AuthProvider(Enum):
    """Supported OAuth 2.0 providers"""
    GOOGLE = "google"
    AZURE = "azure" 
    OKTA = "okta"
    GITHUB = "github"
    CUSTOM = "custom"


@dataclass
class User:
    """User data model"""
    user_id: str
    email: str
    roles: List[UserRole]
    name: str
    provider: AuthProvider
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    last_login: Optional[datetime] = None
    failed_attempts: int = 0
    locked_until: Optional[datetime] = None
    medical_license: Optional[str] = None
    department: Optional[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class AuthSession:
    """Authentication session data"""
    session_id: str
    user_id: str
    roles: List[UserRole]
    issued_at: datetime
    expires_at: datetime
    mfa_verified: bool = False
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    medical_context: Optional[Dict[str, Any]] = None


class VigiaAuthManager:
    """Medical-grade authentication manager"""
    
    def __init__(self):
        """Initialize authentication manager"""
        self.audit = AuditService()
        
        # Password hashing
        if HAS_PASSLIB:
            self.pwd_context = CryptContext(
                schemes=["argon2", "bcrypt"],
                deprecated="auto",
                argon2__memory_cost=65536,  # 64MB
                argon2__time_cost=3,        # 3 iterations
                argon2__parallelism=1       # Single thread
            )
        else:
            self.pwd_context = None
            logger.warning("passlib not available - password hashing disabled")
        
        # JWT settings
        self.jwt_secret = get_secret("JWT_SECRET_KEY")
        self.jwt_algorithm = "HS256"
        self.access_token_expire = timedelta(hours=1)
        self.refresh_token_expire = timedelta(days=7)
        
        # MFA settings
        self.mfa_issuer = "Vigia Medical AI"
        self.mfa_window = 2  # Allow 2 time windows (60 seconds)
        
        # Security settings
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=30)
        self.session_timeout = timedelta(hours=8)
        
        # In-memory storage (should be replaced with database in production)
        self.users = {}
        self.sessions = {}
        self.revoked_tokens = set()
        
    def hash_password(self, password: str) -> str:
        """Hash password securely"""
        if not self.pwd_context:
            # Fallback to basic hashing if passlib not available
            salt = secrets.token_hex(32)
            hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return f"pbkdf2_sha256${salt}${hashed.hex()}"
        
        return self.pwd_context.hash(password)
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        if not self.pwd_context:
            # Fallback verification
            if hashed.startswith("pbkdf2_sha256$"):
                _, salt, stored_hash = hashed.split("$")
                computed_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
                return hmac.compare_digest(stored_hash, computed_hash.hex())
            return False
        
        return self.pwd_context.verify(password, hashed)
    
    def create_user(self, 
                   email: str,
                   password: str,
                   name: str,
                   roles: List[UserRole],
                   provider: AuthProvider = AuthProvider.CUSTOM,
                   medical_license: Optional[str] = None,
                   department: Optional[str] = None) -> User:
        """Create new user account"""
        
        # Check if user already exists
        if any(user.email == email for user in self.users.values()):
            raise ValueError("User with this email already exists")
        
        # Generate user ID
        user_id = secrets.token_urlsafe(16)
        
        # Hash password
        password_hash = self.hash_password(password)
        
        # Create user
        user = User(
            user_id=user_id,
            email=email,
            roles=roles,
            name=name,
            provider=provider,
            medical_license=medical_license,
            department=department
        )
        
        # Store user (in production, this would be in a database)
        self.users[user_id] = {
            "user": user,
            "password_hash": password_hash
        }
        
        # Audit log
        self.audit.log_event(
            event_type=AuditEventType.USER_ACCESS,
            level=AuditLevel.INFO,
            message=f"User created: {email}",
            context={
                "user_id": user_id,
                "email": email,
                "roles": [role.value for role in roles],
                "provider": provider.value,
                "medical_license": medical_license,
                "department": department
            }
        )
        
        return user
    
    def authenticate_user(self, 
                         email: str, 
                         password: str,
                         ip_address: Optional[str] = None,
                         user_agent: Optional[str] = None) -> Optional[User]:
        """Authenticate user with email and password"""
        
        # Find user by email
        user_data = None
        for user_info in self.users.values():
            if user_info["user"].email == email:
                user_data = user_info
                break
        
        if not user_data:
            self.audit.log_event(
                event_type=AuditEventType.AUTHENTICATION_FAILED,
                level=AuditLevel.WARNING,
                message=f"Authentication failed - user not found: {email}",
                context={"email": email, "ip_address": ip_address}
            )
            return None
        
        user = user_data["user"]
        
        # Check if account is locked
        if user.locked_until and datetime.utcnow() < user.locked_until:
            self.audit.log_event(
                event_type=AuditEventType.AUTHENTICATION_FAILED,
                level=AuditLevel.WARNING,
                message=f"Authentication failed - account locked: {email}",
                context={"user_id": user.user_id, "locked_until": user.locked_until.isoformat()}
            )
            return None
        
        # Verify password
        if not self.verify_password(password, user_data["password_hash"]):
            # Increment failed attempts
            user.failed_attempts += 1
            
            # Lock account if too many failures
            if user.failed_attempts >= self.max_failed_attempts:
                user.locked_until = datetime.utcnow() + self.lockout_duration
                
                self.audit.log_event(
                    event_type=AuditEventType.AUTHENTICATION_FAILED,
                    level=AuditLevel.ERROR,
                    message=f"Account locked due to failed attempts: {email}",
                    context={
                        "user_id": user.user_id,
                        "failed_attempts": user.failed_attempts,
                        "locked_until": user.locked_until.isoformat()
                    }
                )
            else:
                self.audit.log_event(
                    event_type=AuditEventType.AUTHENTICATION_FAILED,
                    level=AuditLevel.WARNING,
                    message=f"Authentication failed - invalid password: {email}",
                    context={
                        "user_id": user.user_id,
                        "failed_attempts": user.failed_attempts
                    }
                )
            
            return None
        
        # Reset failed attempts on successful password verification
        user.failed_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        
        self.audit.log_event(
            event_type=AuditEventType.USER_ACCESS,
            level=AuditLevel.INFO,
            message=f"User authenticated: {email}",
            context={
                "user_id": user.user_id,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "mfa_required": user.mfa_enabled
            }
        )
        
        return user
    
    def setup_mfa(self, user_id: str) -> Tuple[str, str]:
        """Set up Multi-Factor Authentication for user"""
        if not HAS_PYOTP:
            raise ImportError("pyotp library required for MFA")
        
        user_data = self.users.get(user_id)
        if not user_data:
            raise ValueError("User not found")
        
        user = user_data["user"]
        
        # Generate secret
        secret = pyotp.random_base32()
        
        # Create provisioning URI for QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name=self.mfa_issuer
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        # Convert QR code to base64 for display
        from io import BytesIO
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode()
        
        # Store secret (not yet enabled)
        user.mfa_secret = secret
        user.mfa_enabled = False
        
        self.audit.log_event(
            event_type=AuditEventType.DATA_MODIFIED,
            level=AuditLevel.INFO,
            message=f"MFA setup initiated: {user.email}",
            context={"user_id": user_id}
        )
        
        return secret, qr_base64
    
    def verify_mfa_setup(self, user_id: str, token: str) -> bool:
        """Verify MFA setup with user-provided token"""
        if not HAS_PYOTP:
            return False
        
        user_data = self.users.get(user_id)
        if not user_data:
            return False
        
        user = user_data["user"]
        
        if not user.mfa_secret:
            return False
        
        # Verify token
        totp = pyotp.TOTP(user.mfa_secret)
        if totp.verify(token, valid_window=self.mfa_window):
            # Enable MFA
            user.mfa_enabled = True
            
            self.audit.log_event(
                event_type=AuditEventType.DATA_MODIFIED,
                level=AuditLevel.INFO,
                message=f"MFA enabled: {user.email}",
                context={"user_id": user_id}
            )
            
            return True
        
        return False
    
    def verify_mfa_token(self, user_id: str, token: str) -> bool:
        """Verify MFA token during login"""
        if not HAS_PYOTP:
            return False
        
        user_data = self.users.get(user_id)
        if not user_data:
            return False
        
        user = user_data["user"]
        
        if not user.mfa_enabled or not user.mfa_secret:
            return False
        
        # Verify token
        totp = pyotp.TOTP(user.mfa_secret)
        verified = totp.verify(token, valid_window=self.mfa_window)
        
        self.audit.log_event(
            event_type=AuditEventType.USER_ACCESS,
            level=AuditLevel.INFO if verified else AuditLevel.WARNING,
            message=f"MFA verification: {user.email} - {'success' if verified else 'failed'}",
            context={"user_id": user_id, "verified": verified}
        )
        
        return verified
    
    def create_session(self, 
                      user: User,
                      mfa_verified: bool = False,
                      ip_address: Optional[str] = None,
                      user_agent: Optional[str] = None,
                      medical_context: Optional[Dict[str, Any]] = None) -> AuthSession:
        """Create authentication session"""
        
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + self.session_timeout
        
        session = AuthSession(
            session_id=session_id,
            user_id=user.user_id,
            roles=user.roles,
            issued_at=datetime.utcnow(),
            expires_at=expires_at,
            mfa_verified=mfa_verified,
            ip_address=ip_address,
            user_agent=user_agent,
            medical_context=medical_context
        )
        
        self.sessions[session_id] = session
        
        self.audit.log_event(
            event_type=AuditEventType.USER_ACCESS,
            level=AuditLevel.INFO,
            message=f"Session created: {user.email}",
            context={
                "session_id": session_id,
                "user_id": user.user_id,
                "expires_at": expires_at.isoformat(),
                "mfa_verified": mfa_verified,
                "medical_context": bool(medical_context)
            }
        )
        
        return session
    
    def create_jwt_token(self, 
                        user: User, 
                        session: AuthSession,
                        token_type: str = "access") -> str:
        """Create JWT token"""
        if not HAS_JWT:
            raise ImportError("PyJWT library required for JWT tokens")
        
        if not self.jwt_secret:
            raise ValueError("JWT secret not configured")
        
        now = datetime.utcnow()
        
        if token_type == "access":
            expires = now + self.access_token_expire
        else:  # refresh
            expires = now + self.refresh_token_expire
        
        payload = {
            "sub": user.user_id,
            "email": user.email,
            "roles": [role.value for role in user.roles],
            "session_id": session.session_id,
            "mfa_verified": session.mfa_verified,
            "iat": now,
            "exp": expires,
            "type": token_type,
            "iss": "vigia-medical-ai",
            "aud": "vigia-medical-clients"
        }
        
        # Add medical context if available
        if session.medical_context:
            payload["medical_context"] = session.medical_context
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        
        return token
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        if not HAS_JWT:
            return None
        
        if not self.jwt_secret:
            return None
        
        try:
            # Check if token is revoked
            if token in self.revoked_tokens:
                return None
            
            payload = jwt.decode(
                token, 
                self.jwt_secret, 
                algorithms=[self.jwt_algorithm],
                audience="vigia-medical-clients",
                issuer="vigia-medical-ai"
            )
            
            # Verify session still exists
            session_id = payload.get("session_id")
            if session_id and session_id not in self.sessions:
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
    
    def revoke_token(self, token: str):
        """Revoke JWT token"""
        self.revoked_tokens.add(token)
        
        # In production, store in database with expiration
        # For now, keep in memory (will be lost on restart)
    
    def logout_session(self, session_id: str):
        """Logout and invalidate session"""
        session = self.sessions.pop(session_id, None)
        
        if session:
            self.audit.log_event(
                event_type=AuditEventType.USER_ACCESS,
                level=AuditLevel.INFO,
                message=f"Session logged out: {session.user_id}",
                context={"session_id": session_id, "user_id": session.user_id}
            )
    
    def require_roles(self, required_roles: List[UserRole], user_roles: List[UserRole]) -> bool:
        """Check if user has required roles"""
        # Super admin can access everything
        if UserRole.SUPER_ADMIN in user_roles:
            return True
        
        # Emergency role can access medical functions
        if UserRole.EMERGENCY in user_roles and any(
            role in [UserRole.PHYSICIAN, UserRole.NURSE, UserRole.SPECIALIST] 
            for role in required_roles
        ):
            return True
        
        # Check if user has any of the required roles
        return any(role in user_roles for role in required_roles)
    
    def require_medical_role(self, user_roles: List[UserRole]) -> bool:
        """Check if user has medical role"""
        medical_roles = [
            UserRole.PHYSICIAN,
            UserRole.SPECIALIST, 
            UserRole.NURSE,
            UserRole.EMERGENCY
        ]
        
        return self.require_roles(medical_roles, user_roles)
    
    def get_user_permissions(self, user_roles: List[UserRole]) -> Dict[str, bool]:
        """Get user permissions based on roles"""
        permissions = {
            "view_medical_data": False,
            "edit_medical_data": False,
            "delete_medical_data": False,
            "admin_access": False,
            "emergency_access": False,
            "audit_access": False,
            "system_config": False
        }
        
        for role in user_roles:
            if role == UserRole.PATIENT:
                permissions["view_medical_data"] = True  # Own data only
            
            elif role == UserRole.NURSE:
                permissions["view_medical_data"] = True
                permissions["edit_medical_data"] = True
            
            elif role in [UserRole.PHYSICIAN, UserRole.SPECIALIST]:
                permissions["view_medical_data"] = True
                permissions["edit_medical_data"] = True
                permissions["delete_medical_data"] = True
            
            elif role == UserRole.EMERGENCY:
                permissions["view_medical_data"] = True
                permissions["edit_medical_data"] = True
                permissions["emergency_access"] = True
            
            elif role == UserRole.ADMIN:
                permissions["admin_access"] = True
                permissions["system_config"] = True
            
            elif role == UserRole.SUPER_ADMIN:
                for key in permissions:
                    permissions[key] = True
            
            elif role == UserRole.AUDIT:
                permissions["audit_access"] = True
                permissions["view_medical_data"] = True  # Read-only
        
        return permissions
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        now = datetime.utcnow()
        expired_sessions = [
            session_id for session_id, session in self.sessions.items()
            if session.expires_at < now
        ]
        
        for session_id in expired_sessions:
            self.logout_session(session_id)
        
        logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")


# Global auth manager instance
_auth_manager = None

def get_auth_manager() -> VigiaAuthManager:
    """Get global auth manager instance"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = VigiaAuthManager()
    return _auth_manager


# OAuth 2.0 Provider Configurations
OAUTH_PROVIDERS = {
    AuthProvider.GOOGLE: {
        "client_id": lambda: get_secret("GOOGLE_OAUTH_CLIENT_ID"),
        "client_secret": lambda: get_secret("GOOGLE_OAUTH_CLIENT_SECRET"),
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
        "scopes": ["openid", "email", "profile"]
    },
    AuthProvider.AZURE: {
        "client_id": lambda: get_secret("AZURE_OAUTH_CLIENT_ID"),
        "client_secret": lambda: get_secret("AZURE_OAUTH_CLIENT_SECRET"),
        "tenant_id": lambda: get_secret("AZURE_TENANT_ID"),
        "auth_url": lambda: f"https://login.microsoftonline.com/{get_secret('AZURE_TENANT_ID')}/oauth2/v2.0/authorize",
        "token_url": lambda: f"https://login.microsoftonline.com/{get_secret('AZURE_TENANT_ID')}/oauth2/v2.0/token",
        "userinfo_url": "https://graph.microsoft.com/v1.0/me",
        "scopes": ["openid", "email", "profile"]
    }
}