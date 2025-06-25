#!/usr/bin/env python3
"""
Encryption Validation Tests - Security Critical
===============================================

Critical tests for encryption security in medical data processing
to ensure patient data protection at rest and in transit.
"""

import pytest
import os
from unittest.mock import Mock, patch
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from vigia_detect.security.encryption import EncryptionManager, MedicalDataEncryption
from vigia_detect.core.phi_tokenization_client import PHITokenizationClient


@pytest.mark.critical
@pytest.mark.security
@pytest.mark.encryption
class TestMedicalDataEncryption:
    """Critical tests for medical data encryption security."""
    
    def test_patient_data_encryption_at_rest(self):
        """Verify patient data is properly encrypted at rest."""
        encryption_manager = EncryptionManager()
        
        # Test patient data encryption
        sensitive_data = {
            "patient_name": "Bruce Wayne",
            "date_of_birth": "1980-02-19",
            "medical_record": "Detailed medical history...",
            "diagnosis": "Stage III pressure ulcer"
        }
        
        # Encrypt sensitive data
        encrypted_data = encryption_manager.encrypt_medical_data(sensitive_data)
        
        # Verify encryption applied
        assert encrypted_data != sensitive_data
        assert "Bruce Wayne" not in str(encrypted_data)
        assert "1980-02-19" not in str(encrypted_data)
        
        # Verify decryption works
        decrypted_data = encryption_manager.decrypt_medical_data(encrypted_data)
        assert decrypted_data == sensitive_data
    
    def test_encryption_key_strength(self):
        """Verify encryption keys meet medical-grade security standards."""
        encryption_manager = EncryptionManager()
        
        # Generate new encryption key
        key = encryption_manager.generate_medical_grade_key()
        
        # Verify key length (256-bit minimum for medical data)
        assert len(key) >= 32  # 256 bits
        
        # Verify key entropy
        key_bytes = bytes(key, 'utf-8') if isinstance(key, str) else key
        unique_bytes = len(set(key_bytes))
        assert unique_bytes >= 20  # High entropy requirement
    
    def test_encryption_key_rotation(self):
        """Verify encryption key rotation maintains data accessibility."""
        encryption_manager = EncryptionManager()
        
        # Original data encryption
        test_data = {"patient_id": "test-001", "medical_data": "sensitive"}
        old_key = encryption_manager.get_current_key()
        encrypted_with_old_key = encryption_manager.encrypt_medical_data(test_data)
        
        # Rotate encryption key
        encryption_manager.rotate_encryption_key()
        new_key = encryption_manager.get_current_key()
        
        # Verify key changed
        assert old_key != new_key
        
        # Verify old encrypted data still accessible
        decrypted_data = encryption_manager.decrypt_with_key_history(encrypted_with_old_key)
        assert decrypted_data == test_data


@pytest.mark.critical
@pytest.mark.security
@pytest.mark.encryption
class TestTransitEncryption:
    """Critical tests for data encryption in transit."""
    
    @pytest.mark.asyncio
    async def test_api_communication_encryption(self):
        """Verify all API communications are encrypted in transit."""
        tokenization_client = PHITokenizationClient()
        
        # Mock HTTPS verification
        with patch('vigia_detect.core.phi_tokenization_client.requests') as mock_requests:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}
            mock_requests.post.return_value = mock_response
            
            # Execute API call
            await tokenization_client.tokenize_patient("MRN-001", {})
            
            # Verify HTTPS used
            call_args = mock_requests.post.call_args
            url = call_args[1]['url'] if 'url' in call_args[1] else call_args[0][0]
            assert url.startswith('https://'), "API communication not using HTTPS"
            
            # Verify TLS verification enabled
            verify_ssl = call_args[1].get('verify', True)
            assert verify_ssl is True, "SSL verification disabled"
    
    def test_database_connection_encryption(self):
        """Verify database connections use encrypted channels."""
        from vigia_detect.db.database_client import DatabaseClient
        
        db_client = DatabaseClient()
        
        # Verify connection string uses SSL
        connection_params = db_client.get_connection_parameters()
        assert 'sslmode=require' in connection_params or 'ssl=true' in connection_params.lower()
        
        # Verify certificate validation
        ssl_config = db_client.get_ssl_configuration()
        assert ssl_config.get('verify_certificates', False) is True


@pytest.mark.critical
@pytest.mark.security
@pytest.mark.encryption
class TestTokenEncryptionSecurity:
    """Critical tests for token encryption and security."""
    
    def test_token_encryption_reversibility(self):
        """Verify tokens can be encrypted/decrypted without data loss."""
        from vigia_detect.security.token_encryption import TokenEncryption
        
        token_encryption = TokenEncryption()
        
        # Test token data
        token_data = {
            "token_id": "test-token-001",
            "patient_alias": "Batman",
            "creation_timestamp": "2025-01-15T10:30:00",
            "expiration_timestamp": "2025-01-16T10:30:00"
        }
        
        # Encrypt token
        encrypted_token = token_encryption.encrypt_token(token_data)
        assert encrypted_token != token_data
        
        # Decrypt token
        decrypted_token = token_encryption.decrypt_token(encrypted_token)
        assert decrypted_token == token_data
    
    def test_token_storage_encryption(self):
        """Verify tokens are encrypted when stored in cache/database."""
        from vigia_detect.utils.cache import TokenCache
        
        cache = TokenCache()
        
        # Store token in cache
        token_id = "test-token-storage-001"
        token_data = {"alias": "Batman", "permissions": ["read"]}
        
        with patch.object(cache, '_encrypt_before_storage') as mock_encrypt:
            mock_encrypt.return_value = b'encrypted_token_data'
            
            cache.set(token_id, token_data)
            
            # Verify encryption called before storage
            mock_encrypt.assert_called_once_with(token_data)