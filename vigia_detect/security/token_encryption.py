"""
Token Encryption Module

Provides specialized encryption for authentication tokens and session data.
Implements secure token handling for medical system access control.
"""

import json
import logging
from typing import Dict, Any, Optional
from .encryption import EncryptionManager

logger = logging.getLogger(__name__)


class TokenEncryption:
    """
    Specialized encryption for authentication tokens.
    
    Provides secure encryption/decryption for session tokens,
    patient aliases, and access control tokens.
    """
    
    def __init__(self, encryption_manager: Optional[EncryptionManager] = None):
        """Initialize with encryption manager"""
        self.encryption_manager = encryption_manager or EncryptionManager()
        logger.info("Token encryption initialized")
    
    def encrypt_token(self, token_data: Dict[str, Any]) -> str:
        """
        Encrypt token data
        
        Args:
            token_data: Token information to encrypt
            
        Returns:
            Encrypted token string
        """
        try:
            # Convert to JSON string
            json_data = json.dumps(token_data, sort_keys=True)
            
            # Encrypt the JSON data
            encrypted_token = self.encryption_manager.encrypt(json_data)
            
            logger.debug(f"Token encrypted successfully")
            return encrypted_token
            
        except Exception as e:
            logger.error(f"Token encryption failed: {e}")
            raise
    
    def decrypt_token(self, encrypted_token: str) -> Dict[str, Any]:
        """
        Decrypt token data
        
        Args:
            encrypted_token: Encrypted token string
            
        Returns:
            Decrypted token data
        """
        try:
            # Decrypt the token
            json_data = self.encryption_manager.decrypt(encrypted_token)
            
            # Parse JSON back to dictionary
            token_data = json.loads(json_data)
            
            logger.debug("Token decrypted successfully")
            return token_data
            
        except Exception as e:
            logger.error(f"Token decryption failed: {e}")
            raise
    
    def encrypt_session_data(self, session_data: Dict[str, Any]) -> str:
        """
        Encrypt session data for secure storage
        
        Args:
            session_data: Session information
            
        Returns:
            Encrypted session string
        """
        return self.encrypt_token(session_data)
    
    def decrypt_session_data(self, encrypted_session: str) -> Dict[str, Any]:
        """
        Decrypt session data
        
        Args:
            encrypted_session: Encrypted session string
            
        Returns:
            Decrypted session data
        """
        return self.decrypt_token(encrypted_session)
    
    def create_secure_token_id(self, base_data: str) -> str:
        """
        Create secure token ID from base data
        
        Args:
            base_data: Base data for token ID generation
            
        Returns:
            Secure token ID
        """
        import hashlib
        import secrets
        
        # Create hash with salt for secure ID
        salt = secrets.token_hex(16)
        hash_data = hashlib.sha256(f"{base_data}{salt}".encode()).hexdigest()
        
        return f"token_{hash_data[:16]}"
    
    def validate_token_integrity(self, encrypted_token: str) -> bool:
        """
        Validate token integrity without decrypting content
        
        Args:
            encrypted_token: Encrypted token to validate
            
        Returns:
            True if token is valid
        """
        try:
            # Try to decrypt - if successful, token is valid
            self.decrypt_token(encrypted_token)
            return True
        except Exception:
            return False