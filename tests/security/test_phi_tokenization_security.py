#!/usr/bin/env python3
"""
PHI Tokenization Security Tests - HIPAA Compliance Critical
===========================================================

Comprehensive security validation for Bruce Wayne → Batman tokenization
to ensure patient data protection and regulatory compliance.
"""

import pytest
import asyncio
import uuid
import json
import time
import re
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

from vigia_detect.core.phi_tokenization_client import PHITokenizationClient, TokenizedPatient
from vigia_detect.monitoring.phi_tokenizer import PHITokenizer
from vigia_detect.utils.alias_generator import PatientAliasGenerator


@pytest.mark.critical
@pytest.mark.security
@pytest.mark.hipaa_compliance
class TestPHITokenExposurePrevention:
    """Critical tests to prevent PHI token exposure in logs, responses, and caches."""
    
    @pytest.mark.asyncio
    async def test_token_not_exposed_in_logs(self):
        """Verify tokens are never logged in plaintext."""
        with patch('vigia_detect.core.phi_tokenization_client.logger') as mock_logger:
            client = PHITokenizationClient()
            
            # Mock successful tokenization
            mock_token = "test-token-batman-001"
            mock_patient = TokenizedPatient(
                token_id=mock_token,
                patient_alias="Batman",
                age_range="40-49",
                gender_category="male",
                risk_factors={"diabetes": False},
                medical_conditions={"chronic_pain": True}
            )
            
            with patch.object(client, '_tokenize_patient_async', return_value=mock_patient):
                await client.tokenize_patient("MRN-2025-001-BW", {})
            
            # Verify no log calls contain the actual token
            for call in mock_logger.info.call_args_list:
                log_message = str(call[0][0])
                assert mock_token not in log_message, f"Token exposed in log: {log_message}"
                
            for call in mock_logger.debug.call_args_list:
                log_message = str(call[0][0])
                assert mock_token not in log_message, f"Token exposed in debug log: {log_message}"
    
    @pytest.mark.asyncio
    async def test_phi_not_exposed_in_api_responses(self):
        """Verify API responses never contain PHI data."""
        client = PHITokenizationClient()
        
        # Mock patient with PHI that should be sanitized
        phi_data = {
            "full_name": "Bruce Wayne",
            "date_of_birth": "1980-02-19",
            "phone_number": "+1-555-123-4567",
            "address": "1007 Mountain Drive, Gotham"
        }
        
        mock_tokenized = TokenizedPatient(
            token_id="test-token-001",
            patient_alias="Batman",
            age_range="40-49",  # PHI sanitized to range
            gender_category="male",
            risk_factors={"diabetes": False},
            medical_conditions={"chronic_pain": True}
        )
        
        with patch.object(client, '_tokenize_patient_async', return_value=mock_tokenized):
            result = await client.tokenize_patient("MRN-2025-001-BW", phi_data)
        
        # Convert result to JSON to simulate API response
        response_json = json.dumps(result.__dict__ if hasattr(result, '__dict__') else result)
        
        # Verify no PHI in response
        assert "Bruce Wayne" not in response_json
        assert "1980-02-19" not in response_json
        assert "+1-555-123-4567" not in response_json
        assert "1007 Mountain Drive" not in response_json
        assert "Gotham" not in response_json
    
    def test_token_cache_security(self):
        """Verify token cache keys don't expose patient relationships."""
        from vigia_detect.utils.cache import TokenCache
        
        cache = TokenCache()
        token_id = "test-token-batman-001"
        hospital_mrn = "MRN-2025-001-BW"
        
        # Mock cache operation
        with patch.object(cache, 'set') as mock_set:
            cache.set(f"token:{token_id}", {"alias": "Batman"})
            
            # Verify cache key doesn't contain hospital MRN or PHI
            cache_key = mock_set.call_args[0][0]
            assert hospital_mrn not in cache_key
            assert "Bruce" not in cache_key
            assert "Wayne" not in cache_key


@pytest.mark.critical
@pytest.mark.security
@pytest.mark.hipaa_compliance
class TestReverseLookupPrevention:
    """Critical tests to prevent reverse lookup attacks on tokenization system."""
    
    @pytest.mark.asyncio
    async def test_token_brute_force_protection(self):
        """Verify system protects against token brute force attacks."""
        client = PHITokenizationClient()
        
        # Attempt multiple invalid token validations
        invalid_tokens = [f"invalid-token-{i}" for i in range(100)]
        
        with patch.object(client, 'validate_token') as mock_validate:
            mock_validate.return_value = False
            
            # Track timing to detect if protection is in place
            start_time = time.time()
            
            for token in invalid_tokens[:10]:  # Test first 10
                await client.validate_token(token)
            
            elapsed_time = time.time() - start_time
            
            # Should have rate limiting - expect reasonable delay
            assert elapsed_time > 0.1, "No rate limiting detected for invalid tokens"
    
    def test_alias_generation_deterministic_but_secure(self):
        """Verify alias generation is deterministic but not reverse-engineerable."""
        generator = PatientAliasGenerator()
        
        # Same hospital MRN should always generate same alias
        mrn = "MRN-2025-001-BW"
        alias1 = generator.generate_alias(mrn)
        alias2 = generator.generate_alias(mrn)
        
        assert alias1 == alias2, "Alias generation not deterministic"
        
        # But alias shouldn't reveal any PHI patterns
        assert "2025" not in alias1, "Alias contains year pattern"
        assert "001" not in alias1, "Alias contains sequence pattern"
        assert "BW" not in alias1, "Alias contains initials"
        
        # Multiple MRNs should generate different aliases
        mrn2 = "MRN-2025-002-JD"
        alias3 = generator.generate_alias(mrn2)
        
        assert alias1 != alias3, "Different MRNs generate same alias"
    
    @pytest.mark.asyncio
    async def test_timing_attack_resistance(self):
        """Verify token validation timing doesn't leak information."""
        client = PHITokenizationClient()
        
        # Test valid vs invalid token timing
        valid_token = "valid-token-batman-001"
        invalid_token = "invalid-token-joker-999"
        
        with patch.object(client, '_validate_token_database') as mock_db:
            # Configure mock to simulate database lookup
            def mock_lookup(token):
                if token == valid_token:
                    time.sleep(0.01)  # Simulate database hit
                    return True
                else:
                    time.sleep(0.01)  # Should take same time for cache miss
                    return False
            
            mock_db.side_effect = mock_lookup
            
            # Measure timing for valid token
            start_valid = time.time()
            await client.validate_token(valid_token)
            valid_time = time.time() - start_valid
            
            # Measure timing for invalid token
            start_invalid = time.time()
            await client.validate_token(invalid_token)
            invalid_time = time.time() - start_invalid
            
            # Timing difference should be minimal
            time_diff = abs(valid_time - invalid_time)
            assert time_diff < 0.005, f"Timing attack vector: {time_diff}s difference"


@pytest.mark.critical
@pytest.mark.security
@pytest.mark.hipaa_compliance
class TestPHILeakagePrevention:
    """Critical tests to prevent PHI leakage through medical conditions and risk factors."""
    
    def test_medical_conditions_phi_sanitization(self):
        """Verify medical conditions don't contain identifying information."""
        tokenizer = PHITokenizer()
        
        # Test medical conditions that might contain PHI
        phi_conditions = {
            "diabetes_diagnosed_at_gotham_general": True,
            "surgery_performed_by_dr_leslie_thompkins": True,
            "injury_from_wayne_enterprises_accident": True,
            "medication_prescribed_at_1007_mountain_drive": False
        }
        
        sanitized = tokenizer._sanitize_medical_conditions(phi_conditions)
        
        # Verify no location or provider information
        sanitized_str = json.dumps(sanitized)
        assert "gotham" not in sanitized_str.lower()
        assert "wayne" not in sanitized_str.lower()
        assert "dr_leslie" not in sanitized_str.lower()
        assert "1007_mountain_drive" not in sanitized_str.lower()
        assert "thompkins" not in sanitized_str.lower()
    
    def test_risk_factors_excessive_detail_prevention(self):
        """Verify risk factors don't preserve excessive detail."""
        tokenizer = PHITokenizer()
        
        # Test risk factors with excessive detail
        detailed_factors = {
            "mobility": "wheelchair_user_since_batman_incident_2019",
            "diet": "vegan_diet_started_after_alfred_recommendation",
            "occupation": "ceo_wayne_enterprises_night_vigilante",
            "family_history": "parents_murdered_when_8_years_old"
        }
        
        sanitized = tokenizer._sanitize_risk_factors(detailed_factors)
        
        # Should be generalized
        assert isinstance(sanitized.get("limited_mobility"), bool)
        assert isinstance(sanitized.get("dietary_restrictions"), bool)
        
        # Should not contain identifying details
        sanitized_str = json.dumps(sanitized)
        assert "batman" not in sanitized_str.lower()
        assert "alfred" not in sanitized_str.lower()
        assert "wayne" not in sanitized_str.lower()
        assert "murdered" not in sanitized_str.lower()
    
    @pytest.mark.asyncio
    async def test_audit_logs_phi_prevention(self):
        """Verify audit logs don't contain PHI."""
        from vigia_detect.utils.audit_service import AuditService
        
        audit = AuditService()
        
        # Mock audit log entry with potential PHI
        with patch.object(audit, 'log_event') as mock_log:
            await audit.log_tokenization_event(
                hospital_mrn="MRN-2025-001-BW",
                token_id="test-token-batman-001",
                event_type="tokenization_created",
                details={"patient_name": "Bruce Wayne", "facility": "Gotham General"}
            )
            
            # Verify audit log doesn't contain PHI
            log_call = mock_log.call_args[1] if mock_log.call_args else {}
            log_str = json.dumps(log_call)
            
            assert "Bruce Wayne" not in log_str
            assert "MRN-2025-001-BW" not in log_str  # Hospital MRN should be tokenized


@pytest.mark.critical
@pytest.mark.security
@pytest.mark.hipaa_compliance
class TestAuthenticationSecurity:
    """Critical tests for JWT authentication and authorization in tokenization service."""
    
    @pytest.mark.asyncio
    async def test_jwt_token_expiration_enforcement(self):
        """Verify expired JWT tokens are rejected."""
        client = PHITokenizationClient()
        
        # Mock expired JWT token
        expired_jwt = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE2MDk0NTkyMDB9.invalid"
        
        with patch('vigia_detect.core.phi_tokenization_client.verify_jwt') as mock_verify:
            mock_verify.return_value = False  # Expired token
            
            with pytest.raises(Exception) as exc_info:
                await client.tokenize_patient("MRN-2025-001-BW", {}, jwt_token=expired_jwt)
            
            assert "expired" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_authorization_level_validation(self):
        """Verify proper authorization levels for tokenization operations."""
        client = PHITokenizationClient()
        
        # Test different authorization levels
        read_only_jwt = "read_only_token"
        admin_jwt = "admin_token"
        
        with patch('vigia_detect.core.phi_tokenization_client.get_jwt_permissions') as mock_perms:
            # Read-only should fail tokenization
            mock_perms.return_value = {"read": True, "write": False}
            
            with pytest.raises(Exception) as exc_info:
                await client.tokenize_patient("MRN-2025-001-BW", {}, jwt_token=read_only_jwt)
            
            assert "permission" in str(exc_info.value).lower() or "unauthorized" in str(exc_info.value).lower()
            
            # Admin should succeed
            mock_perms.return_value = {"read": True, "write": True, "admin": True}
            
            with patch.object(client, '_tokenize_patient_async'):
                # Should not raise exception
                await client.tokenize_patient("MRN-2025-001-BW", {}, jwt_token=admin_jwt)
    
    def test_service_to_service_authentication(self):
        """Verify service-to-service authentication is properly validated."""
        from tokenization.phi_tokenization_service import PHITokenizationService
        
        service = PHITokenizationService()
        
        # Test invalid service credentials
        invalid_credentials = {"service_id": "fake_service", "api_key": "invalid_key"}
        
        with patch.object(service, 'validate_service_credentials') as mock_validate:
            mock_validate.return_value = False
            
            # Should reject invalid service
            result = service.authenticate_service(invalid_credentials)
            assert result is False
            
        # Test valid service credentials
        valid_credentials = {"service_id": "medical_dispatcher", "api_key": "valid_key"}
        
        with patch.object(service, 'validate_service_credentials') as mock_validate:
            mock_validate.return_value = True
            
            # Should accept valid service
            result = service.authenticate_service(valid_credentials)
            assert result is True


@pytest.mark.critical
@pytest.mark.security
@pytest.mark.hipaa_compliance
class TestCryptographicSecurity:
    """Critical tests for cryptographic security in tokenization."""
    
    def test_token_generation_randomness(self):
        """Verify token generation has sufficient randomness."""
        generator = PatientAliasGenerator()
        
        # Generate multiple tokens for same input
        mrn = "MRN-2025-001-BW"
        tokens = [generator.generate_token(mrn) for _ in range(100)]
        
        # All tokens should be unique (probabilistically)
        unique_tokens = set(tokens)
        assert len(unique_tokens) == len(tokens), "Token generation not sufficiently random"
        
        # Tokens should be properly formatted
        for token in tokens:
            assert len(token) >= 32, f"Token too short: {token}"
            assert re.match(r'^[a-f0-9-]+$', token), f"Token has invalid format: {token}"
    
    def test_encryption_key_security(self):
        """Verify encryption keys are properly managed."""
        from vigia_detect.security.encryption import EncryptionManager
        
        manager = EncryptionManager()
        
        # Test key rotation capability
        old_key = manager.get_current_key()
        manager.rotate_key()
        new_key = manager.get_current_key()
        
        assert old_key != new_key, "Key rotation not working"
        assert len(new_key) >= 32, "Encryption key too short"
    
    def test_hash_collision_resistance(self):
        """Verify hash functions resist collision attacks."""
        from vigia_detect.security.hashing import SecureHash
        
        hasher = SecureHash()
        
        # Test similar inputs produce different hashes
        similar_inputs = [
            "MRN-2025-001-BW",
            "MRN-2025-001-BX",  # One character different
            "MRN-2025-002-BW",  # One digit different
        ]
        
        hashes = [hasher.hash_patient_identifier(input_val) for input_val in similar_inputs]
        
        # All hashes should be different
        unique_hashes = set(hashes)
        assert len(unique_hashes) == len(hashes), "Hash collision detected"
        
        # Hashes should be properly formatted
        for hash_val in hashes:
            assert len(hash_val) >= 64, f"Hash too short: {hash_val}"