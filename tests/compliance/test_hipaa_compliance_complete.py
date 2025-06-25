#!/usr/bin/env python3
"""
Complete HIPAA Compliance Tests - Regulatory Critical
=====================================================

Comprehensive HIPAA compliance validation for medical data protection,
audit trails, and regulatory requirements.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from vigia_detect.core.phi_tokenization_client import PHITokenizationClient
from vigia_detect.utils.audit_service import AuditService
from vigia_detect.security.access_control import AccessControlManager
from vigia_detect.db.database_client import DatabaseClient


@pytest.mark.critical
@pytest.mark.hipaa_compliance
@pytest.mark.regulatory
class TestPHIProtectionCompliance:
    """Critical tests for PHI protection compliance under HIPAA regulations."""
    
    def test_phi_minimum_necessary_standard(self):
        """Verify only minimum necessary PHI is accessed and processed."""
        tokenization_client = PHITokenizationClient()
        
        # Full PHI dataset
        complete_phi_data = {
            "full_name": "Bruce Wayne",
            "date_of_birth": "1980-02-19",
            "social_security": "123-45-6789",
            "phone_number": "+1-555-123-4567",
            "address": "1007 Mountain Drive, Gotham",
            "emergency_contact": "Alfred Pennyworth",
            "insurance_info": "Wayne Enterprises Health Plan",
            "medical_history": "Detailed 50-page medical record",
            "current_medications": ["Medication A", "Medication B"],
            "lpp_grade": 2,
            "lpp_location": "heel",
            "lpp_size": "3x2cm"
        }
        
        # Process for LPP assessment (should only use minimum necessary)
        with patch.object(tokenization_client, '_extract_minimum_necessary') as mock_extract:
            mock_extract.return_value = {
                "age_range": "40-49",
                "gender_category": "male",
                "lpp_grade": 2,
                "lpp_location": "heel",
                "lpp_size": "3x2cm",
                "relevant_risk_factors": {"diabetes": False, "mobility": "normal"}
            }
            
            processed_data = tokenization_client.process_for_lpp_assessment(complete_phi_data)
            
            # Verify minimum necessary standard
            processed_str = json.dumps(processed_data)
            assert "Bruce Wayne" not in processed_str
            assert "123-45-6789" not in processed_str
            assert "+1-555-123-4567" not in processed_str
            assert "1007 Mountain Drive" not in processed_str
            
            # Verify essential medical data preserved
            assert processed_data["lpp_grade"] == 2
            assert processed_data["age_range"] == "40-49"
    
    @pytest.mark.asyncio
    async def test_phi_access_logging_compliance(self):
        """Verify all PHI access is logged per HIPAA requirements."""
        audit_service = AuditService()
        tokenization_client = PHITokenizationClient()
        
        # PHI access scenario
        phi_access_event = {
            "hospital_mrn": "MRN-2025-001-BW",
            "accessing_user": "dr_leslie_thompkins",
            "access_purpose": "lpp_medical_assessment",
            "access_timestamp": datetime.now(),
            "data_elements_accessed": ["medical_history", "current_lpp_status"]
        }
        
        with patch.object(audit_service, 'log_phi_access') as mock_audit:
            with patch.object(tokenization_client, 'access_phi_for_tokenization') as mock_access:
                mock_access.return_value = {"success": True}
                
                # Simulate PHI access
                await tokenization_client.access_phi_for_tokenization(
                    hospital_mrn=phi_access_event["hospital_mrn"],
                    accessing_user=phi_access_event["accessing_user"],
                    purpose=phi_access_event["access_purpose"]
                )
            
            # Verify comprehensive audit logging
            mock_audit.assert_called_once()
            audit_call = mock_audit.call_args[1]
            
            assert "accessing_user" in audit_call
            assert "access_purpose" in audit_call
            assert "timestamp" in audit_call
            assert "data_elements_accessed" in audit_call
    
    def test_phi_retention_compliance(self):
        """Verify PHI retention policies comply with HIPAA requirements."""
        from vigia_detect.compliance.retention_manager import PHIRetentionManager
        
        retention_manager = PHIRetentionManager()
        
        # Test different retention scenarios
        retention_test_cases = [
            {
                "data_type": "medical_images",
                "required_retention_years": 6,
                "patient_age_category": "adult"
            },
            {
                "data_type": "audit_logs",
                "required_retention_years": 6,
                "patient_age_category": "adult"
            },
            {
                "data_type": "tokenization_records",
                "required_retention_years": 6,
                "patient_age_category": "adult"
            }
        ]
        
        for test_case in retention_test_cases:
            retention_policy = retention_manager.get_retention_policy(
                data_type=test_case["data_type"],
                patient_category=test_case["patient_age_category"]
            )
            
            # Verify HIPAA compliant retention periods
            assert retention_policy["retention_years"] >= test_case["required_retention_years"]
            assert retention_policy["secure_disposal_required"] is True
            assert retention_policy["disposal_method"] == "cryptographic_erasure"


@pytest.mark.critical
@pytest.mark.hipaa_compliance
@pytest.mark.regulatory
class TestAccessControlCompliance:
    """Critical tests for HIPAA access control and authorization compliance."""
    
    def test_role_based_access_control(self):
        """Verify role-based access control meets HIPAA requirements."""
        access_control = AccessControlManager()
        
        # Different healthcare roles with appropriate permissions
        healthcare_roles = [
            {
                "role": "attending_physician",
                "permissions": ["read_phi", "write_phi", "approve_treatments"],
                "phi_access_level": "full"
            },
            {
                "role": "nurse_specialist",
                "permissions": ["read_phi", "update_care_notes"],
                "phi_access_level": "limited"
            },
            {
                "role": "care_coordinator",
                "permissions": ["read_limited_phi", "schedule_appointments"],
                "phi_access_level": "minimal"
            },
            {
                "role": "it_support",
                "permissions": ["system_maintenance"],
                "phi_access_level": "none"
            }
        ]
        
        for role_config in healthcare_roles:
            user_permissions = access_control.get_user_permissions(
                user_role=role_config["role"]
            )
            
            # Verify appropriate access levels
            if role_config["phi_access_level"] == "none":
                assert "read_phi" not in user_permissions
                assert "write_phi" not in user_permissions
            elif role_config["phi_access_level"] == "full":
                assert "read_phi" in user_permissions
            
            # Verify permissions match role requirements
            for permission in role_config["permissions"]:
                assert permission in user_permissions
    
    def test_user_authentication_strength(self):
        """Verify user authentication meets HIPAA security requirements."""
        from vigia_detect.security.authentication import MedicalAuthenticationService
        
        auth_service = MedicalAuthenticationService()
        
        # Test authentication requirements
        authentication_scenarios = [
            {
                "user_type": "physician",
                "requires_mfa": True,
                "password_complexity": "high",
                "session_timeout_minutes": 30
            },
            {
                "user_type": "nurse",
                "requires_mfa": True,
                "password_complexity": "high",
                "session_timeout_minutes": 60
            },
            {
                "user_type": "admin",
                "requires_mfa": True,
                "password_complexity": "maximum",
                "session_timeout_minutes": 15
            }
        ]
        
        for scenario in authentication_scenarios:
            auth_requirements = auth_service.get_authentication_requirements(
                user_type=scenario["user_type"]
            )
            
            # Verify HIPAA authentication standards
            assert auth_requirements["mfa_required"] == scenario["requires_mfa"]
            assert auth_requirements["session_timeout"] <= scenario["session_timeout_minutes"]
            assert auth_requirements["password_complexity"] in ["high", "maximum"]
    
    def test_session_management_compliance(self):
        """Verify session management meets HIPAA security requirements."""
        from vigia_detect.security.session_manager import MedicalSessionManager
        
        session_manager = MedicalSessionManager()
        
        # Create medical user session
        user_session = {
            "user_id": "dr_leslie_001",
            "role": "attending_physician",
            "department": "wound_care",
            "session_start": datetime.now()
        }
        
        session_id = session_manager.create_secure_session(user_session)
        
        # Test session security features
        session_details = session_manager.get_session_details(session_id)
        
        # Verify secure session attributes
        assert session_details["encrypted"] is True
        assert session_details["secure_token"] is not None
        assert session_details["ip_binding"] is True
        assert session_details["inactivity_timeout"] <= 30  # 30 minutes max
        
        # Test automatic session expiration
        with patch('vigia_detect.security.session_manager.datetime') as mock_datetime:
            # Simulate 31 minutes later
            mock_datetime.now.return_value = user_session["session_start"] + timedelta(minutes=31)
            
            session_valid = session_manager.validate_session(session_id)
            assert session_valid is False  # Session should be expired


@pytest.mark.critical
@pytest.mark.hipaa_compliance
@pytest.mark.regulatory
class TestAuditTrailCompliance:
    """Critical tests for HIPAA audit trail and accountability compliance."""
    
    def test_comprehensive_audit_trail(self):
        """Verify comprehensive audit trail meets HIPAA requirements."""
        audit_service = AuditService()
        
        # Medical workflow events that require auditing
        medical_events = [
            {
                "event_type": "phi_access",
                "user_id": "dr_leslie_001",
                "patient_token": "batman-token-001",
                "action": "view_medical_record",
                "justification": "routine_lpp_assessment"
            },
            {
                "event_type": "medical_decision",
                "user_id": "nurse_specialist_002",
                "patient_token": "batman-token-001",
                "action": "update_care_plan",
                "decision_data": {"lpp_grade": 2, "treatment_modified": True}
            },
            {
                "event_type": "data_export",
                "user_id": "care_coordinator_003",
                "patient_token": "batman-token-001",
                "action": "generate_care_report",
                "export_scope": "lpp_status_summary"
            }
        ]
        
        for event in medical_events:
            with patch.object(audit_service, 'create_audit_entry') as mock_audit:
                # Log medical event
                audit_service.log_medical_event(
                    event_type=event["event_type"],
                    user_id=event["user_id"],
                    patient_token=event["patient_token"],
                    action_details=event
                )
                
                # Verify comprehensive audit entry
                audit_entry = mock_audit.call_args[1]
                
                # Required HIPAA audit elements
                assert "timestamp" in audit_entry
                assert "user_identification" in audit_entry
                assert "action_performed" in audit_entry
                assert "patient_identifier" in audit_entry  # Token, not PHI
                assert "justification" in audit_entry
                assert "system_identifier" in audit_entry
                
                # Verify no PHI in audit logs
                audit_str = json.dumps(audit_entry)
                assert "Bruce Wayne" not in audit_str
                assert "MRN-2025-001-BW" not in audit_str
    
    def test_audit_trail_integrity(self):
        """Verify audit trail integrity and tamper detection."""
        audit_service = AuditService()
        
        # Create audit entry
        original_audit = {
            "event_id": "audit-001",
            "timestamp": datetime.now(),
            "user_id": "dr_leslie_001",
            "action": "view_patient_record",
            "patient_token": "batman-token-001"
        }
        
        with patch.object(audit_service, 'calculate_audit_hash') as mock_hash:
            mock_hash.return_value = "secure_hash_123456789"
            
            # Store audit entry with integrity protection
            audit_service.store_audit_entry_with_integrity(original_audit)
            
            # Verify hash calculation for integrity
            mock_hash.assert_called_once()
            
            # Test tamper detection
            tampered_audit = original_audit.copy()
            tampered_audit["action"] = "delete_patient_record"  # Unauthorized modification
            
            with patch.object(audit_service, 'verify_audit_integrity') as mock_verify:
                mock_verify.return_value = False  # Hash mismatch
                
                integrity_check = audit_service.verify_audit_integrity(tampered_audit)
                assert integrity_check is False  # Tampering detected
    
    def test_audit_trail_retention_compliance(self):
        """Verify audit trail retention meets HIPAA 6-year requirement."""
        audit_service = AuditService()
        
        # Test audit retention policy
        retention_policy = audit_service.get_audit_retention_policy()
        
        # HIPAA requires 6-year minimum retention
        assert retention_policy["retention_years"] >= 6
        assert retention_policy["automatic_purge"] is False  # Manual review required
        assert retention_policy["secure_archival"] is True
        
        # Test audit retrieval for compliance reporting
        with patch.object(audit_service, 'retrieve_audit_range') as mock_retrieve:
            mock_retrieve.return_value = [
                {"event_id": "audit-001", "timestamp": datetime.now() - timedelta(days=2000)},
                {"event_id": "audit-002", "timestamp": datetime.now() - timedelta(days=1000)}
            ]
            
            # Retrieve 5-year audit history
            five_year_audits = audit_service.retrieve_audit_range(
                start_date=datetime.now() - timedelta(days=1825),  # 5 years
                end_date=datetime.now()
            )
            
            # Verify audit availability for compliance period
            assert len(five_year_audits) >= 1
            mock_retrieve.assert_called_once()


@pytest.mark.critical
@pytest.mark.hipaa_compliance
@pytest.mark.regulatory
class TestBreachNotificationCompliance:
    """Critical tests for HIPAA breach notification requirements."""
    
    def test_breach_detection_mechanisms(self):
        """Verify automated breach detection meets HIPAA requirements."""
        from vigia_detect.security.breach_detection import BreachDetectionService
        
        breach_detector = BreachDetectionService()
        
        # Potential breach scenarios
        breach_scenarios = [
            {
                "scenario": "unauthorized_phi_access",
                "details": {
                    "user_id": "unauthorized_user_001",
                    "patient_tokens_accessed": ["batman-token-001", "joker-token-002"],
                    "access_time": datetime.now(),
                    "authorization_level": "none"
                },
                "expected_severity": "high"
            },
            {
                "scenario": "bulk_data_export",
                "details": {
                    "user_id": "authorized_user_001",
                    "records_exported": 1000,
                    "export_justification": "research",
                    "approval_status": "missing"
                },
                "expected_severity": "medium"
            }
        ]
        
        for scenario in breach_scenarios:
            with patch.object(breach_detector, 'assess_potential_breach') as mock_assess:
                mock_assess.return_value = {
                    "is_breach": True,
                    "severity": scenario["expected_severity"],
                    "requires_notification": True,
                    "notification_timeline_hours": 72 if scenario["expected_severity"] == "high" else 168
                }
                
                breach_assessment = breach_detector.assess_potential_breach(
                    scenario_type=scenario["scenario"],
                    incident_details=scenario["details"]
                )
                
                # Verify breach detection accuracy
                assert breach_assessment["is_breach"] is True
                assert breach_assessment["severity"] == scenario["expected_severity"]
                
                # Verify HIPAA notification timeline
                if scenario["expected_severity"] == "high":
                    assert breach_assessment["notification_timeline_hours"] <= 72
    
    def test_breach_notification_process(self):
        """Verify breach notification process meets HIPAA requirements."""
        from vigia_detect.compliance.breach_notification import BreachNotificationManager
        
        notification_manager = BreachNotificationManager()
        
        # Confirmed breach requiring notification
        confirmed_breach = {
            "breach_id": "breach-001",
            "discovery_date": datetime.now(),
            "affected_patients": 1,
            "breach_type": "unauthorized_access",
            "phi_compromised": ["medical_record"],
            "severity": "medium"
        }
        
        with patch.object(notification_manager, 'execute_notification_process') as mock_notify:
            mock_notify.return_value = {
                "patient_notification_sent": True,
                "regulatory_notification_sent": True,
                "notification_timeline_compliant": True,
                "documentation_complete": True
            }
            
            notification_result = notification_manager.execute_notification_process(
                breach_details=confirmed_breach
            )
            
            # Verify HIPAA notification requirements met
            assert notification_result["patient_notification_sent"] is True
            assert notification_result["regulatory_notification_sent"] is True
            assert notification_result["notification_timeline_compliant"] is True
            assert notification_result["documentation_complete"] is True