"""
Access Control Module

Provides role-based access control (RBAC) for medical system components.
Implements HIPAA-compliant access policies for healthcare data.
"""

import os
import logging
from typing import Dict, List, Set, Optional, Any
from enum import Enum
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class Role(Enum):
    """System roles with hierarchical permissions"""
    SYSTEM_ADMIN = "system_admin"
    MEDICAL_DIRECTOR = "medical_director"
    PHYSICIAN = "physician"
    NURSE = "nurse"
    TECHNICIAN = "technician"
    PATIENT = "patient"
    GUEST = "guest"


class Permission(Enum):
    """System permissions for medical operations"""
    # Data access permissions
    READ_PHI = "read_phi"
    WRITE_PHI = "write_phi"
    DELETE_PHI = "delete_phi"
    
    # Medical operations
    MEDICAL_DIAGNOSIS = "medical_diagnosis"
    MEDICAL_TREATMENT = "medical_treatment"
    MEDICAL_REVIEW = "medical_review"
    
    # System operations
    SYSTEM_CONFIG = "system_config"
    USER_MANAGEMENT = "user_management"
    AUDIT_ACCESS = "audit_access"
    
    # Image processing
    PROCESS_MEDICAL_IMAGES = "process_medical_images"
    AI_MODEL_ACCESS = "ai_model_access"
    
    # Communication
    PATIENT_COMMUNICATION = "patient_communication"
    MEDICAL_TEAM_COMMUNICATION = "medical_team_communication"


class AccessControlManager:
    """
    Medical-grade access control manager.
    
    Implements role-based access control with audit logging
    for HIPAA compliance.
    """
    
    # Role-permission mappings
    ROLE_PERMISSIONS = {
        Role.SYSTEM_ADMIN: {
            Permission.READ_PHI, Permission.WRITE_PHI, Permission.DELETE_PHI,
            Permission.MEDICAL_DIAGNOSIS, Permission.MEDICAL_TREATMENT, Permission.MEDICAL_REVIEW,
            Permission.SYSTEM_CONFIG, Permission.USER_MANAGEMENT, Permission.AUDIT_ACCESS,
            Permission.PROCESS_MEDICAL_IMAGES, Permission.AI_MODEL_ACCESS,
            Permission.PATIENT_COMMUNICATION, Permission.MEDICAL_TEAM_COMMUNICATION
        },
        Role.MEDICAL_DIRECTOR: {
            Permission.READ_PHI, Permission.WRITE_PHI,
            Permission.MEDICAL_DIAGNOSIS, Permission.MEDICAL_TREATMENT, Permission.MEDICAL_REVIEW,
            Permission.PROCESS_MEDICAL_IMAGES, Permission.AI_MODEL_ACCESS,
            Permission.PATIENT_COMMUNICATION, Permission.MEDICAL_TEAM_COMMUNICATION,
            Permission.AUDIT_ACCESS
        },
        Role.PHYSICIAN: {
            Permission.READ_PHI, Permission.WRITE_PHI,
            Permission.MEDICAL_DIAGNOSIS, Permission.MEDICAL_TREATMENT, Permission.MEDICAL_REVIEW,
            Permission.PROCESS_MEDICAL_IMAGES, Permission.AI_MODEL_ACCESS,
            Permission.PATIENT_COMMUNICATION, Permission.MEDICAL_TEAM_COMMUNICATION
        },
        Role.NURSE: {
            Permission.READ_PHI, Permission.WRITE_PHI,
            Permission.MEDICAL_REVIEW,
            Permission.PROCESS_MEDICAL_IMAGES,
            Permission.PATIENT_COMMUNICATION, Permission.MEDICAL_TEAM_COMMUNICATION
        },
        Role.TECHNICIAN: {
            Permission.READ_PHI,
            Permission.PROCESS_MEDICAL_IMAGES,
            Permission.MEDICAL_TEAM_COMMUNICATION
        },
        Role.PATIENT: {
            Permission.PATIENT_COMMUNICATION
        },
        Role.GUEST: set()  # No permissions by default
    }
    
    def __init__(self):
        """Initialize access control manager"""
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.access_log: List[Dict[str, Any]] = []
        self.failed_attempts: Dict[str, List[datetime]] = {}
        
        # Load configuration
        self.session_timeout = timedelta(hours=8)  # Medical sessions timeout
        self.max_failed_attempts = 3
        self.lockout_duration = timedelta(minutes=30)
        
        logger.info("Access control manager initialized")
    
    def authenticate_user(self, user_id: str, role: Role, 
                         additional_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Authenticate user and create session
        
        Args:
            user_id: User identifier
            role: User role
            additional_context: Additional authentication context
            
        Returns:
            Session token
        """
        try:
            # Check if user is locked out
            if self._is_user_locked_out(user_id):
                self._log_access_attempt(user_id, "authentication", False, "User locked out")
                raise PermissionError(f"User {user_id} is temporarily locked out")
            
            # Create session
            session_token = self._generate_session_token()
            session_data = {
                'user_id': user_id,
                'role': role,
                'created_at': datetime.utcnow(),
                'last_activity': datetime.utcnow(),
                'context': additional_context or {}
            }
            
            self.active_sessions[session_token] = session_data
            self._log_access_attempt(user_id, "authentication", True, f"Role: {role.value}")
            
            logger.info(f"User {user_id} authenticated with role {role.value}")
            return session_token
            
        except Exception as e:
            self._log_access_attempt(user_id, "authentication", False, str(e))
            raise
    
    def check_permission(self, session_token: str, permission: Permission, 
                        resource_context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check if user has permission for specific operation
        
        Args:
            session_token: Active session token
            permission: Required permission
            resource_context: Context about the resource being accessed
            
        Returns:
            True if permission granted
        """
        try:
            # Validate session
            session = self._validate_session(session_token)
            if not session:
                return False
            
            user_id = session['user_id']
            role = session['role']
            
            # Check role permissions
            role_permissions = self.ROLE_PERMISSIONS.get(role, set())
            has_permission = permission in role_permissions
            
            # Log access attempt
            self._log_access_attempt(
                user_id, 
                f"permission_check:{permission.value}", 
                has_permission,
                f"Role: {role.value}, Resource: {resource_context}"
            )
            
            if has_permission:
                # Update last activity
                session['last_activity'] = datetime.utcnow()
            
            return has_permission
            
        except Exception as e:
            logger.error(f"Permission check failed: {e}")
            return False
    
    def require_permission(self, session_token: str, permission: Permission,
                          resource_context: Optional[Dict[str, Any]] = None):
        """
        Require permission or raise exception
        
        Args:
            session_token: Active session token
            permission: Required permission
            resource_context: Context about the resource being accessed
            
        Raises:
            PermissionError: If permission not granted
        """
        if not self.check_permission(session_token, permission, resource_context):
            session = self.active_sessions.get(session_token)
            user_id = session['user_id'] if session else 'unknown'
            role = session['role'].value if session else 'unknown'
            
            error_msg = f"Permission denied: {user_id} (role: {role}) lacks {permission.value}"
            logger.warning(error_msg)
            raise PermissionError(error_msg)
    
    def logout_user(self, session_token: str):
        """Logout user and invalidate session"""
        try:
            session = self.active_sessions.get(session_token)
            if session:
                user_id = session['user_id']
                self._log_access_attempt(user_id, "logout", True, "Session terminated")
                logger.info(f"User {user_id} logged out")
                
            # Remove session
            self.active_sessions.pop(session_token, None)
            
        except Exception as e:
            logger.error(f"Logout failed: {e}")
    
    def get_user_permissions(self, session_token: str) -> Set[Permission]:
        """Get all permissions for authenticated user"""
        session = self._validate_session(session_token)
        if not session:
            return set()
        
        role = session['role']
        return self.ROLE_PERMISSIONS.get(role, set())
    
    def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get all active sessions (admin only)"""
        # Clean expired sessions first
        self._cleanup_expired_sessions()
        
        # Return sanitized session data
        sanitized_sessions = {}
        for token, session in self.active_sessions.items():
            sanitized_sessions[token] = {
                'user_id': session['user_id'],
                'role': session['role'].value,
                'created_at': session['created_at'].isoformat(),
                'last_activity': session['last_activity'].isoformat()
            }
        
        return sanitized_sessions
    
    def _validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Validate session token and check expiration"""
        session = self.active_sessions.get(session_token)
        if not session:
            return None
        
        # Check session timeout
        if datetime.utcnow() - session['last_activity'] > self.session_timeout:
            self.logout_user(session_token)
            return None
        
        return session
    
    def _is_user_locked_out(self, user_id: str) -> bool:
        """Check if user is locked out due to failed attempts"""
        failed_attempts = self.failed_attempts.get(user_id, [])
        
        # Remove old attempts
        cutoff_time = datetime.utcnow() - self.lockout_duration
        recent_attempts = [attempt for attempt in failed_attempts if attempt > cutoff_time]
        self.failed_attempts[user_id] = recent_attempts
        
        return len(recent_attempts) >= self.max_failed_attempts
    
    def _generate_session_token(self) -> str:
        """Generate secure session token"""
        import secrets
        return secrets.token_urlsafe(32)
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions"""
        expired_tokens = []
        cutoff_time = datetime.utcnow() - self.session_timeout
        
        for token, session in self.active_sessions.items():
            if session['last_activity'] < cutoff_time:
                expired_tokens.append(token)
        
        for token in expired_tokens:
            session = self.active_sessions[token]
            logger.info(f"Session expired for user {session['user_id']}")
            self.active_sessions.pop(token)
    
    def _log_access_attempt(self, user_id: str, operation: str, success: bool, details: str):
        """Log access attempt for audit trail"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'operation': operation,
            'success': success,
            'details': details,
            'ip_address': os.getenv('REMOTE_ADDR', 'unknown')
        }
        
        self.access_log.append(log_entry)
        
        # Track failed attempts for lockout
        if not success and operation == "authentication":
            if user_id not in self.failed_attempts:
                self.failed_attempts[user_id] = []
            self.failed_attempts[user_id].append(datetime.utcnow())
        
        logger.info(f"Access log: {operation} {'SUCCESS' if success else 'FAILED'} for {user_id}")
    
    def get_audit_log(self, user_id: Optional[str] = None, 
                     start_time: Optional[datetime] = None,
                     end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get access audit log
        
        Args:
            user_id: Filter by user ID
            start_time: Filter by start time
            end_time: Filter by end time
            
        Returns:
            Filtered audit log entries
        """
        filtered_log = self.access_log.copy()
        
        if user_id:
            filtered_log = [entry for entry in filtered_log if entry['user_id'] == user_id]
        
        if start_time:
            start_str = start_time.isoformat()
            filtered_log = [entry for entry in filtered_log if entry['timestamp'] >= start_str]
        
        if end_time:
            end_str = end_time.isoformat()
            filtered_log = [entry for entry in filtered_log if entry['timestamp'] <= end_str]
        
        return filtered_log
    
    def export_audit_log(self, filepath: str):
        """Export audit log to file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.access_log, f, indent=2, default=str)
            logger.info(f"Audit log exported to {filepath}")
        except Exception as e:
            logger.error(f"Failed to export audit log: {e}")
            raise