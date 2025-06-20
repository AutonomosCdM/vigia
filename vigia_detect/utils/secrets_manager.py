"""
Production Secrets Management for Vigia Medical AI System
Secure secrets handling with cloud provider integration
HIPAA-compliant secrets management with proper rotation and audit trails
"""

import os
import json
import base64
import logging
from typing import Dict, Optional, Any, Union, List
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path

try:
    import keyring
    HAS_KEYRING = True
except ImportError:
    HAS_KEYRING = False

try:
    import boto3
    from botocore.exceptions import ClientError
    HAS_AWS = True
except ImportError:
    HAS_AWS = False

try:
    from google.cloud import secretmanager
    HAS_GOOGLE_SECRETS = True
except ImportError:
    HAS_GOOGLE_SECRETS = False

from .audit_service import AuditService, AuditEventType, AuditLevel

logger = logging.getLogger(__name__)


class SecretsManagerBase(ABC):
    """Abstract base class for secrets management"""
    
    @abstractmethod
    def get_secret(self, key: str) -> Optional[str]:
        """Get secret value by key"""
        pass
    
    @abstractmethod
    def set_secret(self, key: str, value: str) -> bool:
        """Set secret value"""
        pass
    
    @abstractmethod
    def delete_secret(self, key: str) -> bool:
        """Delete secret"""
        pass
    
    @abstractmethod
    def list_secrets(self) -> List[str]:
        """List available secret keys"""
        pass
    
    @abstractmethod
    def rotate_secret(self, key: str, new_value: str) -> bool:
        """Rotate secret with new value"""
        pass


class LocalSecretsManager(SecretsManagerBase):
    """Local development secrets manager using keyring"""
    
    def __init__(self, service_name: str = "vigia-medical"):
        """Initialize local secrets manager"""
        if not HAS_KEYRING:
            raise ImportError("keyring library required for local secrets management")
        
        self.service_name = service_name
        self.audit = AuditService()
    
    def get_secret(self, key: str) -> Optional[str]:
        """Get secret from keyring"""
        try:
            secret = keyring.get_password(self.service_name, key)
            if secret:
                self.audit.log_event(
                    event_type=AuditEventType.DATA_ACCESS,
                    level=AuditLevel.INFO,
                    message=f"Secret accessed: {key}",
                    context={"secret_key": key, "source": "keyring"}
                )
            return secret
        except Exception as e:
            logger.error(f"Failed to get secret {key}: {e}")
            return None
    
    def set_secret(self, key: str, value: str) -> bool:
        """Set secret in keyring"""
        try:
            keyring.set_password(self.service_name, key, value)
            self.audit.log_event(
                event_type=AuditEventType.DATA_CREATED,
                level=AuditLevel.INFO,
                message=f"Secret stored: {key}",
                context={"secret_key": key, "source": "keyring"}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to set secret {key}: {e}")
            return False
    
    def delete_secret(self, key: str) -> bool:
        """Delete secret from keyring"""
        try:
            keyring.delete_password(self.service_name, key)
            self.audit.log_event(
                event_type=AuditEventType.DATA_DELETED,
                level=AuditLevel.WARNING,
                message=f"Secret deleted: {key}",
                context={"secret_key": key, "source": "keyring"}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete secret {key}: {e}")
            return False
    
    def list_secrets(self) -> List[str]:
        """List secrets (not directly supported by keyring)"""
        logger.warning("Listing secrets not supported by keyring backend")
        return []
    
    def rotate_secret(self, key: str, new_value: str) -> bool:
        """Rotate secret with audit trail"""
        old_exists = self.get_secret(key) is not None
        if self.set_secret(key, new_value):
            self.audit.log_event(
                event_type=AuditEventType.DATA_MODIFIED,
                level=AuditLevel.WARNING,
                message=f"Secret rotated: {key}",
                context={
                    "secret_key": key, 
                    "source": "keyring",
                    "was_existing": old_exists
                }
            )
            return True
        return False


class AWSSecretsManager(SecretsManagerBase):
    """AWS Secrets Manager implementation"""
    
    def __init__(self, region_name: str = "us-east-1", prefix: str = "vigia/"):
        """Initialize AWS Secrets Manager"""
        if not HAS_AWS:
            raise ImportError("boto3 library required for AWS Secrets Manager")
        
        self.client = boto3.client('secretsmanager', region_name=region_name)
        self.prefix = prefix
        self.audit = AuditService()
    
    def _get_secret_name(self, key: str) -> str:
        """Get full secret name with prefix"""
        return f"{self.prefix}{key}"
    
    def get_secret(self, key: str) -> Optional[str]:
        """Get secret from AWS Secrets Manager"""
        secret_name = self._get_secret_name(key)
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            self.audit.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                level=AuditLevel.INFO,
                message=f"Secret accessed: {key}",
                context={"secret_key": key, "source": "aws_secrets_manager"}
            )
            return response['SecretString']
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.warning(f"Secret not found: {secret_name}")
            else:
                logger.error(f"Failed to get secret {secret_name}: {e}")
            return None
    
    def set_secret(self, key: str, value: str) -> bool:
        """Set secret in AWS Secrets Manager"""
        secret_name = self._get_secret_name(key)
        try:
            # Try to update existing secret first
            try:
                self.client.update_secret(
                    SecretId=secret_name,
                    SecretString=value
                )
                action = "updated"
            except ClientError:
                # Create new secret if update fails
                self.client.create_secret(
                    Name=secret_name,
                    SecretString=value,
                    Description=f"Vigia Medical AI secret: {key}"
                )
                action = "created"
            
            self.audit.log_event(
                event_type=AuditEventType.DATA_CREATED,
                level=AuditLevel.INFO,
                message=f"Secret {action}: {key}",
                context={"secret_key": key, "source": "aws_secrets_manager", "action": action}
            )
            return True
        except ClientError as e:
            logger.error(f"Failed to set secret {secret_name}: {e}")
            return False
    
    def delete_secret(self, key: str) -> bool:
        """Delete secret from AWS Secrets Manager"""
        secret_name = self._get_secret_name(key)
        try:
            self.client.delete_secret(
                SecretId=secret_name,
                ForceDeleteWithoutRecovery=True
            )
            self.audit.log_event(
                event_type=AuditEventType.DATA_DELETED,
                level=AuditLevel.WARNING,
                message=f"Secret deleted: {key}",
                context={"secret_key": key, "source": "aws_secrets_manager"}
            )
            return True
        except ClientError as e:
            logger.error(f"Failed to delete secret {secret_name}: {e}")
            return False
    
    def list_secrets(self) -> List[str]:
        """List secrets with prefix"""
        try:
            paginator = self.client.get_paginator('list_secrets')
            secrets = []
            for page in paginator.paginate():
                for secret in page['SecretList']:
                    name = secret['Name']
                    if name.startswith(self.prefix):
                        secrets.append(name[len(self.prefix):])
            return secrets
        except ClientError as e:
            logger.error(f"Failed to list secrets: {e}")
            return []
    
    def rotate_secret(self, key: str, new_value: str) -> bool:
        """Rotate secret with version control"""
        secret_name = self._get_secret_name(key)
        try:
            self.client.update_secret(
                SecretId=secret_name,
                SecretString=new_value
            )
            self.audit.log_event(
                event_type=AuditEventType.DATA_MODIFIED,
                level=AuditLevel.WARNING,
                message=f"Secret rotated: {key}",
                context={"secret_key": key, "source": "aws_secrets_manager"}
            )
            return True
        except ClientError as e:
            logger.error(f"Failed to rotate secret {secret_name}: {e}")
            return False


class GoogleSecretsManager(SecretsManagerBase):
    """Google Secret Manager implementation"""
    
    def __init__(self, project_id: str, prefix: str = "vigia-"):
        """Initialize Google Secret Manager"""
        if not HAS_GOOGLE_SECRETS:
            raise ImportError("google-cloud-secret-manager required for Google Secrets")
        
        self.client = secretmanager.SecretManagerServiceClient()
        self.project_id = project_id
        self.prefix = prefix
        self.audit = AuditService()
    
    def _get_secret_name(self, key: str) -> str:
        """Get full secret name with prefix"""
        return f"{self.prefix}{key.replace('_', '-').lower()}"
    
    def _get_secret_path(self, key: str) -> str:
        """Get full secret path"""
        secret_name = self._get_secret_name(key)
        return f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
    
    def get_secret(self, key: str) -> Optional[str]:
        """Get secret from Google Secret Manager"""
        try:
            secret_path = self._get_secret_path(key)
            response = self.client.access_secret_version(request={"name": secret_path})
            self.audit.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                level=AuditLevel.INFO,
                message=f"Secret accessed: {key}",
                context={"secret_key": key, "source": "google_secret_manager"}
            )
            return response.payload.data.decode('UTF-8')
        except Exception as e:
            logger.error(f"Failed to get secret {key}: {e}")
            return None
    
    def set_secret(self, key: str, value: str) -> bool:
        """Set secret in Google Secret Manager"""
        secret_name = self._get_secret_name(key)
        try:
            parent = f"projects/{self.project_id}"
            
            # Try to create secret first
            try:
                self.client.create_secret(
                    request={
                        "parent": parent,
                        "secret_id": secret_name,
                        "secret": {"replication": {"automatic": {}}},
                    }
                )
                action = "created"
            except Exception:
                action = "updated"
            
            # Add secret version
            secret_path = f"projects/{self.project_id}/secrets/{secret_name}"
            self.client.add_secret_version(
                request={
                    "parent": secret_path,
                    "payload": {"data": value.encode('UTF-8')},
                }
            )
            
            self.audit.log_event(
                event_type=AuditEventType.DATA_CREATED,
                level=AuditLevel.INFO,
                message=f"Secret {action}: {key}",
                context={"secret_key": key, "source": "google_secret_manager", "action": action}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to set secret {secret_name}: {e}")
            return False
    
    def delete_secret(self, key: str) -> bool:
        """Delete secret from Google Secret Manager"""
        secret_name = self._get_secret_name(key)
        try:
            secret_path = f"projects/{self.project_id}/secrets/{secret_name}"
            self.client.delete_secret(request={"name": secret_path})
            self.audit.log_event(
                event_type=AuditEventType.DATA_DELETED,
                level=AuditLevel.WARNING,
                message=f"Secret deleted: {key}",
                context={"secret_key": key, "source": "google_secret_manager"}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete secret {secret_name}: {e}")
            return False
    
    def list_secrets(self) -> List[str]:
        """List secrets with prefix"""
        try:
            parent = f"projects/{self.project_id}"
            secrets = []
            for secret in self.client.list_secrets(request={"parent": parent}):
                name = secret.name.split('/')[-1]
                if name.startswith(self.prefix):
                    secrets.append(name[len(self.prefix):].replace('-', '_').upper())
            return secrets
        except Exception as e:
            logger.error(f"Failed to list secrets: {e}")
            return []
    
    def rotate_secret(self, key: str, new_value: str) -> bool:
        """Rotate secret by adding new version"""
        return self.set_secret(key, new_value)


class DockerSecretsManager(SecretsManagerBase):
    """Docker secrets manager for container deployments"""
    
    def __init__(self, secrets_path: str = "/run/secrets"):
        """Initialize Docker secrets manager"""
        self.secrets_path = Path(secrets_path)
        self.audit = AuditService()
    
    def get_secret(self, key: str) -> Optional[str]:
        """Get secret from Docker secrets volume"""
        secret_file = self.secrets_path / key.lower()
        try:
            if secret_file.exists():
                with open(secret_file, 'r') as f:
                    secret = f.read().strip()
                self.audit.log_event(
                    event_type=AuditEventType.DATA_ACCESS,
                    level=AuditLevel.INFO,
                    message=f"Secret accessed: {key}",
                    context={"secret_key": key, "source": "docker_secrets"}
                )
                return secret
            return None
        except Exception as e:
            logger.error(f"Failed to read Docker secret {key}: {e}")
            return None
    
    def set_secret(self, key: str, value: str) -> bool:
        """Docker secrets are read-only at runtime"""
        logger.warning("Docker secrets are read-only at runtime")
        return False
    
    def delete_secret(self, key: str) -> bool:
        """Docker secrets are read-only at runtime"""
        logger.warning("Docker secrets are read-only at runtime")
        return False
    
    def list_secrets(self) -> List[str]:
        """List available Docker secrets"""
        try:
            if self.secrets_path.exists():
                return [f.name for f in self.secrets_path.iterdir() if f.is_file()]
            return []
        except Exception as e:
            logger.error(f"Failed to list Docker secrets: {e}")
            return []
    
    def rotate_secret(self, key: str, new_value: str) -> bool:
        """Docker secrets require external rotation"""
        logger.warning("Docker secret rotation requires external orchestration")
        return False


class VigiaSecretsManager:
    """
    Unified secrets manager for Vigia Medical AI System
    Automatically detects environment and uses appropriate backend
    """
    
    def __init__(self, 
                 backend: Optional[str] = None,
                 **kwargs):
        """
        Initialize secrets manager
        
        Args:
            backend: Force specific backend (local, aws, google, docker)
            **kwargs: Backend-specific configuration
        """
        self.audit = AuditService()
        
        # Auto-detect backend if not specified
        if backend is None:
            backend = self._detect_backend()
        
        # Initialize appropriate backend
        if backend == "local":
            self.manager = LocalSecretsManager(**kwargs)
        elif backend == "aws":
            self.manager = AWSSecretsManager(**kwargs)
        elif backend == "google":
            project_id = kwargs.get('project_id') or os.getenv('GOOGLE_CLOUD_PROJECT')
            if not project_id:
                raise ValueError("project_id required for Google Secrets Manager")
            self.manager = GoogleSecretsManager(project_id, **kwargs)
        elif backend == "docker":
            self.manager = DockerSecretsManager(**kwargs)
        else:
            raise ValueError(f"Unknown secrets backend: {backend}")
        
        self.backend_type = backend
        logger.info(f"Initialized secrets manager with {backend} backend")
    
    def _detect_backend(self) -> str:
        """Auto-detect appropriate secrets backend"""
        # Check for Docker secrets
        if Path("/run/secrets").exists():
            return "docker"
        
        # Check for Google Cloud environment
        if os.getenv('GOOGLE_CLOUD_PROJECT'):
            return "google"
        
        # Check for AWS environment
        if os.getenv('AWS_DEFAULT_REGION') or os.getenv('AWS_REGION'):
            return "aws"
        
        # Default to local for development
        return "local"
    
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret with fallback to environment variable"""
        # Try secrets manager first
        secret = self.manager.get_secret(key)
        if secret:
            return secret
        
        # Fallback to environment variable
        env_secret = os.getenv(key)
        if env_secret:
            logger.debug(f"Using environment variable for {key}")
            return env_secret
        
        # Return default if nothing found
        if default is not None:
            logger.debug(f"Using default value for {key}")
            return default
        
        logger.warning(f"Secret not found: {key}")
        return None
    
    def get_required_secret(self, key: str) -> str:
        """Get required secret or raise exception"""
        secret = self.get_secret(key)
        if secret is None:
            raise ValueError(f"Required secret not found: {key}")
        return secret
    
    def set_secret(self, key: str, value: str) -> bool:
        """Set secret value"""
        return self.manager.set_secret(key, value)
    
    def delete_secret(self, key: str) -> bool:
        """Delete secret"""
        return self.manager.delete_secret(key)
    
    def list_secrets(self) -> List[str]:
        """List available secrets"""
        return self.manager.list_secrets()
    
    def rotate_secret(self, key: str, new_value: str) -> bool:
        """Rotate secret with audit trail"""
        success = self.manager.rotate_secret(key, new_value)
        if success:
            self.audit.log_event(
                event_type=AuditEventType.DATA_MODIFIED,
                level=AuditLevel.WARNING,
                message=f"Secret rotation completed: {key}",
                context={
                    "secret_key": key, 
                    "backend": self.backend_type,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        return success
    
    def health_check(self) -> Dict[str, Any]:
        """Check secrets manager health"""
        try:
            # Try to list secrets as health check
            secrets = self.manager.list_secrets()
            return {
                "status": "healthy",
                "backend": self.backend_type,
                "secrets_count": len(secrets),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "backend": self.backend_type,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Global secrets manager instance
_secrets_manager = None

def get_secrets_manager(**kwargs) -> VigiaSecretsManager:
    """Get global secrets manager instance"""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = VigiaSecretsManager(**kwargs)
    return _secrets_manager

def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Convenience function to get secret"""
    return get_secrets_manager().get_secret(key, default)

def get_required_secret(key: str) -> str:
    """Convenience function to get required secret"""
    return get_secrets_manager().get_required_secret(key)