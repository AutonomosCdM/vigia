#!/usr/bin/env python3
"""
Test Dual Database Separation
Valida la separación física entre Hospital PHI Database y Processing Database

Este test:
1. Simula el flujo completo Bruce Wayne → Batman
2. Valida que PHI nunca salga de la base hospitalaria
3. Confirma que solo datos tokenizados llegan al procesamiento
4. Verifica audit trail completo
5. Testea el PHI Tokenization Service
"""

import asyncio
import os
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List

# Import our tokenization client (commented out for standalone test)
# from vigia_detect.core.phi_tokenization_client import (
#     PHITokenizationClient, 
#     TokenizationClientConfig,
#     tokenize_patient_phi
# )

# ===============================================
# 1. TEST CONFIGURATION
# ===============================================

class TestConfig:
    """Test configuration for dual database separation"""
    
    # Test patient data (simulating Bruce Wayne in hospital)
    TEST_HOSPITAL_MRN = "MRN-2025-001-BW"
    TEST_PATIENT_NAME = "Bruce Wayne"
    TEST_EXPECTED_ALIAS = "Batman"  # Expected tokenized alias
    
    # Service endpoints (for when services are running)
    PHI_TOKENIZATION_SERVICE_URL = "http://localhost:8080"
    
    # Test scenarios
    TEST_SCENARIOS = [
        {
            "name": "bruce_wayne_lpp_detection",
            "hospital_mrn": TEST_HOSPITAL_MRN,
            "purpose": "Pressure injury detection and analysis",
            "urgency": "urgent",
            "expected_alias": TEST_EXPECTED_ALIAS
        },
        {
            "name": "emergency_consultation",
            "hospital_mrn": "MRN-2025-002-CK",  # Clark Kent
            "purpose": "Emergency medical consultation",
            "urgency": "emergency",
            "expected_alias": "Superman"
        }
    ]

config = TestConfig()

# ===============================================
# 2. MOCK HOSPITAL DATABASE
# ===============================================

class MockHospitalDatabase:
    """Mock hospital PHI database for testing"""
    
    def __init__(self):
        self.patients = {
            "MRN-2025-001-BW": {
                "patient_id": "ef50ad25-5ee6-4c6c-8e97-c94c348ce6d6",
                "hospital_mrn": "MRN-2025-001-BW",
                "full_name": "Bruce Wayne",
                "date_of_birth": "1980-02-19",
                "gender": "Male",
                "phone_number": "+1-555-BATMAN",
                "chronic_conditions": ["Chronic pain from old injuries", "Sleep disorders"],
                "attending_physician": "Dr. Leslie Thompkins",
                "ward_location": "VIP Ward",
                "room_number": "Room 1A"
            },
            "MRN-2025-002-CK": {
                "patient_id": "12345678-90ab-cdef-1234-567890abcdef",
                "hospital_mrn": "MRN-2025-002-CK",
                "full_name": "Clark Kent",
                "date_of_birth": "1978-06-18",
                "gender": "Male",
                "phone_number": "+1-555-SUPERMAN",
                "chronic_conditions": ["No known conditions"],
                "attending_physician": "Dr. Hamilton",
                "ward_location": "General Ward",
                "room_number": "Room 5B"
            }
        }
        self.tokenization_requests = {}
        self.access_logs = []
    
    def get_patient_phi(self, hospital_mrn: str) -> Optional[Dict[str, Any]]:
        """Get patient PHI (NEVER exposed externally)"""
        return self.patients.get(hospital_mrn)
    
    def create_tokenization_request(self, hospital_mrn: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create tokenization request"""
        patient_phi = self.get_patient_phi(hospital_mrn)
        if not patient_phi:
            raise ValueError(f"Patient not found: {hospital_mrn}")
        
        # Generate token and alias
        token_id = str(uuid.uuid4())
        
        # Deterministic alias generation (for testing)
        if "Bruce Wayne" in patient_phi["full_name"]:
            alias = "Batman"
        elif "Clark Kent" in patient_phi["full_name"]:
            alias = "Superman"
        else:
            alias = f"Patient_{len(self.tokenization_requests) + 1}"
        
        tokenization_request = {
            "request_id": str(uuid.uuid4()),
            "patient_id": patient_phi["patient_id"],
            "hospital_mrn": hospital_mrn,
            "token_id": token_id,
            "token_alias": alias,
            "requesting_system": request_data["requesting_system"],
            "request_purpose": request_data["request_purpose"],
            "approval_status": "approved",
            "expires_at": datetime.now(timezone.utc) + timedelta(days=30),
            "created_at": datetime.now(timezone.utc)
        }
        
        self.tokenization_requests[token_id] = tokenization_request
        
        # Log access
        self.access_logs.append({
            "timestamp": datetime.now(timezone.utc),
            "patient_id": patient_phi["patient_id"],
            "token_id": token_id,
            "access_type": "tokenization",
            "external_system": request_data["requesting_system"],
            "authorized_by": request_data.get("requested_by", "SYSTEM")
        })
        
        return tokenization_request
    
    def validate_token(self, token_id: str) -> Dict[str, Any]:
        """Validate token"""
        request = self.tokenization_requests.get(token_id)
        if not request:
            return {"valid": False, "reason": "Token not found"}
        
        is_expired = request["expires_at"] < datetime.now(timezone.utc)
        return {
            "valid": not is_expired,
            "token_id": token_id,
            "token_alias": request["token_alias"],
            "expires_at": request["expires_at"],
            "status": "expired" if is_expired else "approved"
        }

# ===============================================
# 3. MOCK PROCESSING DATABASE
# ===============================================

class MockProcessingDatabase:
    """Mock processing database (ONLY tokenized data)"""
    
    def __init__(self):
        self.tokenized_patients = {}
        self.medical_images = {}
        self.lpp_detections = {}
        self.audit_logs = []
    
    def create_tokenized_patient(self, tokenized_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create tokenized patient (NO PHI)"""
        
        # Validate that NO PHI is present
        self._validate_no_phi(tokenized_data)
        
        patient_record = {
            "token_id": tokenized_data["token_id"],
            "patient_alias": tokenized_data["patient_alias"],
            "age_range": tokenized_data.get("age_range", "unknown"),
            "gender_category": tokenized_data.get("gender_category", "unknown"),
            "risk_factors": tokenized_data.get("risk_factors", {}),
            "medical_conditions": tokenized_data.get("medical_conditions", {}),
            "created_at": datetime.now(timezone.utc),
            "token_expires_at": tokenized_data["expires_at"]
        }
        
        self.tokenized_patients[tokenized_data["token_id"]] = patient_record
        
        # Log creation
        self.audit_logs.append({
            "timestamp": datetime.now(timezone.utc),
            "event_type": "tokenized_patient_created",
            "token_id": tokenized_data["token_id"],
            "patient_alias": tokenized_data["patient_alias"],
            "success": True
        })
        
        return patient_record
    
    def get_tokenized_patient(self, token_id: str) -> Optional[Dict[str, Any]]:
        """Get tokenized patient (NO PHI)"""
        return self.tokenized_patients.get(token_id)
    
    def _validate_no_phi(self, data: Dict[str, Any]):
        """Validate that data contains NO PHI"""
        phi_indicators = [
            "full_name", "phone_number", "address", "ssn", "mrn",
            "insurance_number", "emergency_contact", "date_of_birth"
        ]
        
        data_str = json.dumps(data, default=str).lower()
        
        for phi_field in phi_indicators:
            if phi_field in data_str:
                raise ValueError(f"PHI detected in processing database: {phi_field}")
        
        # Check for specific PHI values
        phi_values = ["bruce wayne", "clark kent", "+1-555-batman", "+1-555-superman"]
        for phi_value in phi_values:
            if phi_value in data_str:
                raise ValueError(f"PHI value detected: {phi_value}")

# ===============================================
# 4. MOCK TOKENIZATION SERVICE
# ===============================================

class MockTokenizationService:
    """Mock PHI Tokenization Service for testing"""
    
    def __init__(self):
        self.hospital_db = MockHospitalDatabase()
        self.processing_db = MockProcessingDatabase()
        self.request_count = 0
    
    async def tokenize_patient(self, hospital_mrn: str, request_purpose: str, urgency_level: str = "routine") -> Dict[str, Any]:
        """Tokenize patient (Bruce Wayne → Batman)"""
        self.request_count += 1
        
        print(f"\n🔄 TOKENIZATION REQUEST #{self.request_count}")
        print(f"   Hospital MRN: {hospital_mrn}")
        print(f"   Purpose: {request_purpose}")
        print(f"   Urgency: {urgency_level}")
        
        # Step 1: Get PHI from hospital database
        patient_phi = self.hospital_db.get_patient_phi(hospital_mrn)
        if not patient_phi:
            raise ValueError(f"Patient not found in hospital database: {hospital_mrn}")
        
        print(f"   ✅ Found in Hospital DB: {patient_phi['full_name']}")
        
        # Step 2: Create tokenization request
        request_data = {
            "requesting_system": "vigia_lpp_detection",
            "request_purpose": request_purpose,
            "requested_by": "VIGIA_SYSTEM"
        }
        
        tokenization_request = self.hospital_db.create_tokenization_request(hospital_mrn, request_data)
        
        print(f"   🔐 Token Generated: {tokenization_request['token_id']}")
        print(f"   🦸 Patient Alias: {tokenization_request['token_alias']}")
        
        # Step 3: Create tokenized data (NO PHI)
        birth_year = int(patient_phi["date_of_birth"][:4])
        current_year = datetime.now().year
        age = current_year - birth_year
        age_range = f"{(age // 10) * 10}-{(age // 10) * 10 + 9}"
        
        tokenized_data = {
            "token_id": tokenization_request["token_id"],
            "patient_alias": tokenization_request["token_alias"],
            "age_range": age_range,
            "gender_category": patient_phi["gender"],
            "risk_factors": self._extract_risk_factors(patient_phi["chronic_conditions"]),
            "medical_conditions": self._sanitize_medical_conditions(patient_phi["chronic_conditions"]),
            "expires_at": tokenization_request["expires_at"]
        }
        
        # Step 4: Store in processing database (validate NO PHI)
        processing_record = self.processing_db.create_tokenized_patient(tokenized_data)
        
        print(f"   ✅ Stored in Processing DB (NO PHI)")
        print(f"   📊 Age Range: {tokenized_data['age_range']}")
        print(f"   ⚕️ Risk Factors: {tokenized_data['risk_factors']}")
        
        return {
            "success": True,
            "token_id": tokenized_data["token_id"],
            "patient_alias": tokenized_data["patient_alias"],
            "tokenized_data": tokenized_data,
            "expires_at": tokenized_data["expires_at"],
            "hospital_record_exists": True,
            "processing_record_created": True
        }
    
    async def validate_token(self, token_id: str) -> Dict[str, Any]:
        """Validate token"""
        return self.hospital_db.validate_token(token_id)
    
    def _extract_risk_factors(self, chronic_conditions: list) -> Dict[str, Any]:
        """Extract risk factors from conditions"""
        conditions_str = " ".join(chronic_conditions).lower()
        
        return {
            "diabetes": "diabetes" in conditions_str,
            "limited_mobility": any(term in conditions_str for term in ["mobility", "wheelchair", "bedridden"]),
            "chronic_pain": "pain" in conditions_str,
            "sleep_disorders": "sleep" in conditions_str
        }
    
    def _sanitize_medical_conditions(self, chronic_conditions: list) -> Dict[str, Any]:
        """Sanitize medical conditions (remove any potential PHI)"""
        conditions_str = " ".join(chronic_conditions).lower()
        
        sanitized = {}
        if "pain" in conditions_str:
            sanitized["chronic_pain"] = True
        if "sleep" in conditions_str:
            sanitized["sleep_disorders"] = True
        if "diabetes" in conditions_str:
            sanitized["diabetes"] = True
        
        return sanitized
    
    def get_hospital_audit_trail(self, token_id: str) -> List[Dict[str, Any]]:
        """Get hospital audit trail"""
        return [log for log in self.hospital_db.access_logs if log.get("token_id") == token_id]
    
    def get_processing_audit_trail(self, token_id: str) -> List[Dict[str, Any]]:
        """Get processing audit trail"""
        return [log for log in self.processing_db.audit_logs if log.get("token_id") == token_id]

# ===============================================
# 5. SEPARATION VALIDATION TESTS
# ===============================================

class DatabaseSeparationValidator:
    """Validates that PHI separation is working correctly"""
    
    def __init__(self, tokenization_service: MockTokenizationService):
        self.service = tokenization_service
        self.test_results = []
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all separation validation tests"""
        print("🧪 STARTING DUAL DATABASE SEPARATION TESTS")
        print("=" * 60)
        
        test_methods = [
            self.test_bruce_wayne_tokenization,
            self.test_phi_never_leaves_hospital_db,
            self.test_processing_db_contains_no_phi,
            self.test_token_validation,
            self.test_audit_trail_completeness,
            self.test_clark_kent_tokenization,
            self.test_multiple_patient_isolation
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
                self.test_results.append({"test": test_method.__name__, "status": "PASSED", "error": None})
            except Exception as e:
                self.test_results.append({"test": test_method.__name__, "status": "FAILED", "error": str(e)})
                print(f"   ❌ FAILED: {e}")
        
        return self._generate_test_report()
    
    async def test_bruce_wayne_tokenization(self):
        """Test 1: Bruce Wayne → Batman tokenization"""
        print("\n🦇 TEST 1: Bruce Wayne → Batman Tokenization")
        
        result = await self.service.tokenize_patient(
            hospital_mrn="MRN-2025-001-BW",
            request_purpose="Pressure injury detection and analysis",
            urgency_level="urgent"
        )
        
        # Validate results
        assert result["success"] is True, "Tokenization should succeed"
        assert result["patient_alias"] == "Batman", f"Expected Batman, got {result['patient_alias']}"
        assert "Bruce Wayne" not in str(result["tokenized_data"]), "PHI should not be in tokenized data"
        
        print("   ✅ PASSED: Bruce Wayne successfully tokenized to Batman")
    
    async def test_phi_never_leaves_hospital_db(self):
        """Test 2: PHI never leaves hospital database"""
        print("\n🏥 TEST 2: PHI Isolation in Hospital Database")
        
        # Get hospital patient record
        hospital_record = self.service.hospital_db.get_patient_phi("MRN-2025-001-BW")
        
        # Get processing patient record  
        token_id = list(self.service.hospital_db.tokenization_requests.keys())[0]
        processing_record = self.service.processing_db.get_tokenized_patient(token_id)
        
        # Validate PHI is only in hospital DB
        assert "Bruce Wayne" in hospital_record["full_name"], "Hospital DB should contain real name"
        assert "Bruce Wayne" not in str(processing_record), "Processing DB should NOT contain real name"
        assert hospital_record["phone_number"] == "+1-555-BATMAN", "Hospital DB should contain real phone"
        assert "+1-555-BATMAN" not in str(processing_record), "Processing DB should NOT contain real phone"
        
        print("   ✅ PASSED: PHI properly isolated in hospital database only")
    
    async def test_processing_db_contains_no_phi(self):
        """Test 3: Processing database contains NO PHI"""
        print("\n🤖 TEST 3: Processing Database PHI Validation")
        
        # Get all processing records
        processing_records = self.service.processing_db.tokenized_patients
        
        for token_id, record in processing_records.items():
            # Check for PHI indicators
            record_str = json.dumps(record, default=str).lower()
            
            phi_violations = []
            
            # Names
            if "bruce wayne" in record_str:
                phi_violations.append("Real name found")
            if "clark kent" in record_str:
                phi_violations.append("Real name found")
            
            # Phone numbers
            if "+1-555-batman" in record_str:
                phi_violations.append("Real phone found")
            if "+1-555-superman" in record_str:
                phi_violations.append("Real phone found")
            
            # MRNs
            if "mrn-2025-001-bw" in record_str:
                phi_violations.append("Hospital MRN found")
            
            assert len(phi_violations) == 0, f"PHI violations found: {phi_violations}"
        
        print(f"   ✅ PASSED: {len(processing_records)} processing records contain NO PHI")
    
    async def test_token_validation(self):
        """Test 4: Token validation works correctly"""
        print("\n🔐 TEST 4: Token Validation")
        
        # Get existing token
        token_id = list(self.service.hospital_db.tokenization_requests.keys())[0]
        
        # Validate token
        validation_result = await self.service.validate_token(token_id)
        
        assert validation_result["valid"] is True, "Token should be valid"
        assert validation_result["token_alias"] == "Batman", "Should return correct alias"
        
        # Test invalid token
        fake_token = str(uuid.uuid4())
        fake_validation = await self.service.validate_token(fake_token)
        assert fake_validation["valid"] is False, "Fake token should be invalid"
        
        print("   ✅ PASSED: Token validation working correctly")
    
    async def test_audit_trail_completeness(self):
        """Test 5: Complete audit trail exists"""
        print("\n📋 TEST 5: Audit Trail Completeness")
        
        token_id = list(self.service.hospital_db.tokenization_requests.keys())[0]
        
        # Check hospital audit trail
        hospital_audit = self.service.get_hospital_audit_trail(token_id)
        assert len(hospital_audit) > 0, "Hospital audit trail should exist"
        
        # Check processing audit trail
        processing_audit = self.service.get_processing_audit_trail(token_id)
        assert len(processing_audit) > 0, "Processing audit trail should exist"
        
        # Validate audit content
        hospital_entry = hospital_audit[0]
        assert hospital_entry["access_type"] == "tokenization", "Should log tokenization access"
        assert hospital_entry["external_system"] == "vigia_lpp_detection", "Should log requesting system"
        
        processing_entry = processing_audit[0]
        assert processing_entry["event_type"] == "tokenized_patient_created", "Should log patient creation"
        assert processing_entry["success"] is True, "Should log success"
        
        print(f"   ✅ PASSED: Complete audit trail exists (Hospital: {len(hospital_audit)}, Processing: {len(processing_audit)})")
    
    async def test_clark_kent_tokenization(self):
        """Test 6: Clark Kent → Superman tokenization"""
        print("\n🦸 TEST 6: Clark Kent → Superman Tokenization")
        
        result = await self.service.tokenize_patient(
            hospital_mrn="MRN-2025-002-CK",
            request_purpose="Emergency medical consultation",
            urgency_level="emergency"
        )
        
        assert result["success"] is True, "Tokenization should succeed"
        assert result["patient_alias"] == "Superman", f"Expected Superman, got {result['patient_alias']}"
        assert "Clark Kent" not in str(result["tokenized_data"]), "PHI should not be in tokenized data"
        
        print("   ✅ PASSED: Clark Kent successfully tokenized to Superman")
    
    async def test_multiple_patient_isolation(self):
        """Test 7: Multiple patients properly isolated"""
        print("\n👥 TEST 7: Multiple Patient Isolation")
        
        # Should have two patients now (Bruce Wayne and Clark Kent)
        hospital_patients = len(self.service.hospital_db.patients)
        processing_patients = len(self.service.processing_db.tokenized_patients)
        
        assert hospital_patients == 2, f"Expected 2 hospital patients, got {hospital_patients}"
        assert processing_patients == 2, f"Expected 2 processing patients, got {processing_patients}"
        
        # Validate aliases are different
        aliases = [
            record["patient_alias"] 
            for record in self.service.processing_db.tokenized_patients.values()
        ]
        
        assert "Batman" in aliases, "Batman alias should exist"
        assert "Superman" in aliases, "Superman alias should exist"
        assert len(set(aliases)) == len(aliases), "All aliases should be unique"
        
        print(f"   ✅ PASSED: {processing_patients} patients properly isolated with unique aliases: {aliases}")
    
    def _generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        passed_tests = [r for r in self.test_results if r["status"] == "PASSED"]
        failed_tests = [r for r in self.test_results if r["status"] == "FAILED"]
        
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        print(f"✅ PASSED: {len(passed_tests)}/{len(self.test_results)} tests")
        print(f"❌ FAILED: {len(failed_tests)}/{len(self.test_results)} tests")
        
        if failed_tests:
            print("\nFAILED TESTS:")
            for test in failed_tests:
                print(f"   ❌ {test['test']}: {test['error']}")
        
        print("\nDATABASE SEPARATION STATUS:")
        print(f"   🏥 Hospital PHI Records: {len(self.service.hospital_db.patients)}")
        print(f"   🤖 Processing Records: {len(self.service.processing_db.tokenized_patients)}")
        print(f"   🔐 Active Tokens: {len(self.service.hospital_db.tokenization_requests)}")
        print(f"   📋 Hospital Audit Logs: {len(self.service.hospital_db.access_logs)}")
        print(f"   📋 Processing Audit Logs: {len(self.service.processing_db.audit_logs)}")
        
        success_rate = len(passed_tests) / len(self.test_results) * 100
        
        return {
            "success_rate": success_rate,
            "total_tests": len(self.test_results),
            "passed_tests": len(passed_tests),
            "failed_tests": len(failed_tests),
            "test_results": self.test_results,
            "database_stats": {
                "hospital_phi_records": len(self.service.hospital_db.patients),
                "processing_records": len(self.service.processing_db.tokenized_patients),
                "active_tokens": len(self.service.hospital_db.tokenization_requests),
                "hospital_audit_logs": len(self.service.hospital_db.access_logs),
                "processing_audit_logs": len(self.service.processing_db.audit_logs)
            }
        }

# ===============================================
# 6. MAIN TEST EXECUTION
# ===============================================

async def main():
    """Run dual database separation tests"""
    
    print("🏥 VIGIA DUAL DATABASE SEPARATION TEST")
    print("=" * 60)
    print("Testing: Hospital PHI Database ↔ Processing Database separation")
    print("Scenario: Bruce Wayne → Batman tokenization with complete PHI isolation")
    print()
    
    # Initialize mock tokenization service
    tokenization_service = MockTokenizationService()
    
    # Initialize validator
    validator = DatabaseSeparationValidator(tokenization_service)
    
    # Run all tests
    test_report = await validator.run_all_tests()
    
    # Final summary
    print("\n" + "🎯 FINAL VALIDATION" + "="*40)
    
    if test_report["success_rate"] == 100:
        print("🎉 ALL TESTS PASSED - Database separation is working correctly!")
        print("✅ PHI properly isolated in hospital database")
        print("✅ Processing database contains only tokenized data")
        print("✅ Bruce Wayne → Batman conversion successful")
        print("✅ Complete audit trail maintained")
        print("✅ Token validation working")
        print("✅ Multiple patient isolation confirmed")
    else:
        print(f"⚠️  {test_report['failed_tests']} tests failed - Review separation implementation")
    
    print(f"\n📊 Success Rate: {test_report['success_rate']:.1f}%")
    print(f"📈 Tests Passed: {test_report['passed_tests']}/{test_report['total_tests']}")
    
    return test_report

if __name__ == "__main__":
    # Run the tests
    test_results = asyncio.run(main())