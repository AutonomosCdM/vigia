"""
Authentication Endpoints for Vigia Medical AI System
OAuth 2.0 and MFA endpoints with medical-grade security
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, EmailStr, validator
import secrets
import urllib.parse

try:
    from vigia_detect.utils.auth_manager import (
        get_auth_manager, VigiaAuthManager, UserRole, AuthProvider, User
    )
    from vigia_detect.utils.secrets_manager import get_secret
    from vigia_detect.utils.audit_service import AuditService, AuditEventType, AuditLevel
    HAS_AUTH = True
except ImportError:
    HAS_AUTH = False

logger = logging.getLogger(__name__)

# Security schemes
security = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Pydantic models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    mfa_token: Optional[str] = None

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    medical_license: Optional[str] = None
    department: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v

class MFASetupResponse(BaseModel):
    secret: str
    qr_code: str
    backup_codes: List[str]

class MFAVerifyRequest(BaseModel):
    token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_info: Dict[str, Any]

class UserInfo(BaseModel):
    user_id: str
    email: str
    name: str
    roles: List[str]
    permissions: Dict[str, bool]
    mfa_enabled: bool
    last_login: Optional[str]
    medical_license: Optional[str]
    department: Optional[str]

# Create router
auth_router = APIRouter(prefix="/auth", tags=["authentication"])

if not HAS_AUTH:
    logger.error("Auth components not available - authentication disabled")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user from JWT token"""
    if not HAS_AUTH:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Authentication not available"
        )
    
    auth_manager = get_auth_manager()
    token = credentials.credentials
    
    payload = auth_manager.verify_jwt_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload

def require_roles(required_roles: List[UserRole]):
    """Dependency to require specific roles"""
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        if not HAS_AUTH:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Authentication not available"
            )
        
        user_roles = [UserRole(role) for role in current_user.get("roles", [])]
        auth_manager = get_auth_manager()
        
        if not auth_manager.require_roles(required_roles, user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return current_user
    
    return role_checker

def require_medical_role():
    """Dependency to require medical role"""
    def medical_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        if not HAS_AUTH:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Authentication not available"
            )
        
        user_roles = [UserRole(role) for role in current_user.get("roles", [])]
        auth_manager = get_auth_manager()
        
        if not auth_manager.require_medical_role(user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Medical role required"
            )
        
        return current_user
    
    return medical_checker

def require_mfa():
    """Dependency to require MFA verification"""
    def mfa_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        if not current_user.get("mfa_verified", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="MFA verification required"
            )
        
        return current_user
    
    return mfa_checker

@auth_router.post("/register", response_model=UserInfo)
async def register_user(
    request: RegisterRequest,
    http_request: Request
):
    """Register new user account"""
    if not HAS_AUTH:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Authentication not available"
        )
    
    auth_manager = get_auth_manager()
    
    try:
        # Determine roles based on medical license
        roles = [UserRole.PATIENT]  # Default role
        if request.medical_license:
            if "MD" in request.medical_license.upper():
                roles = [UserRole.PHYSICIAN]
            elif "RN" in request.medical_license.upper():
                roles = [UserRole.NURSE]
            else:
                roles = [UserRole.SPECIALIST]
        
        # Create user
        user = auth_manager.create_user(
            email=request.email,
            password=request.password,
            name=request.name,
            roles=roles,
            medical_license=request.medical_license,
            department=request.department
        )
        
        # Get permissions
        permissions = auth_manager.get_user_permissions(user.roles)
        
        return UserInfo(
            user_id=user.user_id,
            email=user.email,
            name=user.name,
            roles=[role.value for role in user.roles],
            permissions=permissions,
            mfa_enabled=user.mfa_enabled,
            last_login=user.last_login.isoformat() if user.last_login else None,
            medical_license=user.medical_license,
            department=user.department
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@auth_router.post("/login", response_model=TokenResponse)
async def login_user(
    request: LoginRequest,
    http_request: Request
):
    """Authenticate user and return tokens"""
    if not HAS_AUTH:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Authentication not available"
        )
    
    auth_manager = get_auth_manager()
    
    # Get client info
    ip_address = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")
    
    # Authenticate user
    user = auth_manager.authenticate_user(
        email=request.email,
        password=request.password,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Check MFA requirement
    mfa_verified = True
    if user.mfa_enabled:
        if not request.mfa_token:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="MFA token required",
                headers={"X-MFA-Required": "true"}
            )
        
        mfa_verified = auth_manager.verify_mfa_token(user.user_id, request.mfa_token)
        if not mfa_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA token"
            )
    
    # Create session
    session = auth_manager.create_session(
        user=user,
        mfa_verified=mfa_verified,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    # Generate tokens
    access_token = auth_manager.create_jwt_token(user, session, "access")
    refresh_token = auth_manager.create_jwt_token(user, session, "refresh")
    
    # Get permissions
    permissions = auth_manager.get_user_permissions(user.roles)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=int(auth_manager.access_token_expire.total_seconds()),
        user_info={
            "user_id": user.user_id,
            "email": user.email,
            "name": user.name,
            "roles": [role.value for role in user.roles],
            "permissions": permissions,
            "mfa_enabled": user.mfa_enabled,
            "medical_license": user.medical_license,
            "department": user.department
        }
    )

@auth_router.post("/logout")
async def logout_user(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Logout current user"""
    if not HAS_AUTH:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Authentication not available"
        )
    
    auth_manager = get_auth_manager()
    session_id = current_user.get("session_id")
    
    if session_id:
        auth_manager.logout_session(session_id)
    
    return {"message": "Logged out successfully"}

@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Refresh access token using refresh token"""
    if not HAS_AUTH:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Authentication not available"
        )
    
    auth_manager = get_auth_manager()
    refresh_token = credentials.credentials
    
    # Verify refresh token
    payload = auth_manager.verify_jwt_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Get user and session
    user_id = payload.get("sub")
    session_id = payload.get("session_id")
    
    user_data = auth_manager.users.get(user_id)
    session = auth_manager.sessions.get(session_id)
    
    if not user_data or not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found"
        )
    
    user = user_data["user"]
    
    # Generate new access token
    access_token = auth_manager.create_jwt_token(user, session, "access")
    
    # Get permissions
    permissions = auth_manager.get_user_permissions(user.roles)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,  # Keep same refresh token
        expires_in=int(auth_manager.access_token_expire.total_seconds()),
        user_info={
            "user_id": user.user_id,
            "email": user.email,
            "name": user.name,
            "roles": [role.value for role in user.roles],
            "permissions": permissions,
            "mfa_enabled": user.mfa_enabled,
            "medical_license": user.medical_license,
            "department": user.department
        }
    )

@auth_router.get("/me", response_model=UserInfo)
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information"""
    if not HAS_AUTH:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Authentication not available"
        )
    
    auth_manager = get_auth_manager()
    user_id = current_user.get("sub")
    
    user_data = auth_manager.users.get(user_id)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = user_data["user"]
    permissions = auth_manager.get_user_permissions(user.roles)
    
    return UserInfo(
        user_id=user.user_id,
        email=user.email,
        name=user.name,
        roles=[role.value for role in user.roles],
        permissions=permissions,
        mfa_enabled=user.mfa_enabled,
        last_login=user.last_login.isoformat() if user.last_login else None,
        medical_license=user.medical_license,
        department=user.department
    )

@auth_router.post("/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Set up Multi-Factor Authentication"""
    if not HAS_AUTH:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Authentication not available"
        )
    
    auth_manager = get_auth_manager()
    user_id = current_user.get("sub")
    
    try:
        secret, qr_code = auth_manager.setup_mfa(user_id)
        
        # Generate backup codes
        backup_codes = [secrets.token_hex(4) for _ in range(10)]
        
        return MFASetupResponse(
            secret=secret,
            qr_code=qr_code,
            backup_codes=backup_codes
        )
        
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="MFA not available - missing dependencies"
        )
    except Exception as e:
        logger.error(f"MFA setup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MFA setup failed"
        )

@auth_router.post("/mfa/verify")
async def verify_mfa_setup(
    request: MFAVerifyRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Verify MFA setup with token"""
    if not HAS_AUTH:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Authentication not available"
        )
    
    auth_manager = get_auth_manager()
    user_id = current_user.get("sub")
    
    if auth_manager.verify_mfa_setup(user_id, request.token):
        return {"message": "MFA enabled successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MFA token"
        )

@auth_router.post("/mfa/disable")
async def disable_mfa(
    request: MFAVerifyRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Disable Multi-Factor Authentication"""
    if not HAS_AUTH:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Authentication not available"
        )
    
    auth_manager = get_auth_manager()
    user_id = current_user.get("sub")
    
    # Verify current MFA token before disabling
    if not auth_manager.verify_mfa_token(user_id, request.token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MFA token"
        )
    
    # Disable MFA
    user_data = auth_manager.users.get(user_id)
    if user_data:
        user = user_data["user"]
        user.mfa_enabled = False
        user.mfa_secret = None
        
        # Audit log
        audit = AuditService()
        audit.log_event(
            event_type=AuditEventType.DATA_MODIFIED,
            level=AuditLevel.WARNING,
            message=f"MFA disabled: {user.email}",
            context={"user_id": user_id}
        )
    
    return {"message": "MFA disabled successfully"}

# OAuth 2.0 endpoints
@auth_router.get("/oauth/{provider}")
async def oauth_login(provider: str, request: Request):
    """Initiate OAuth 2.0 login with provider"""
    if not HAS_AUTH:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Authentication not available"
        )
    
    try:
        provider_enum = AuthProvider(provider.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported OAuth provider"
        )
    
    # OAuth implementation would go here
    # For now, return placeholder
    return {
        "message": f"OAuth login with {provider} not yet implemented",
        "redirect_url": f"/auth/oauth/{provider}/callback"
    }

@auth_router.get("/oauth/{provider}/callback")
async def oauth_callback(provider: str, code: str, state: Optional[str] = None):
    """Handle OAuth 2.0 callback"""
    if not HAS_AUTH:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Authentication not available"
        )
    
    # OAuth callback implementation would go here
    return {"message": f"OAuth callback for {provider} not yet implemented"}

# Admin endpoints
@auth_router.get("/admin/users", dependencies=[Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN]))])
async def list_users(current_user: Dict[str, Any] = Depends(get_current_user)):
    """List all users (admin only)"""
    if not HAS_AUTH:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Authentication not available"
        )
    
    auth_manager = get_auth_manager()
    
    users = []
    for user_data in auth_manager.users.values():
        user = user_data["user"]
        users.append({
            "user_id": user.user_id,
            "email": user.email,
            "name": user.name,
            "roles": [role.value for role in user.roles],
            "mfa_enabled": user.mfa_enabled,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "medical_license": user.medical_license,
            "department": user.department
        })
    
    return {"users": users, "total": len(users)}

@auth_router.post("/admin/users/{user_id}/roles", dependencies=[Depends(require_roles([UserRole.SUPER_ADMIN]))])
async def update_user_roles(
    user_id: str,
    roles: List[str],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update user roles (super admin only)"""
    if not HAS_AUTH:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Authentication not available"
        )
    
    auth_manager = get_auth_manager()
    
    user_data = auth_manager.users.get(user_id)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        new_roles = [UserRole(role) for role in roles]
        user_data["user"].roles = new_roles
        
        # Audit log
        audit = AuditService()
        audit.log_event(
            event_type=AuditEventType.DATA_MODIFIED,
            level=AuditLevel.WARNING,
            message=f"User roles updated: {user_data['user'].email}",
            context={
                "user_id": user_id,
                "new_roles": roles,
                "updated_by": current_user.get("email")
            }
        )
        
        return {"message": "User roles updated successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {e}"
        )