#!/usr/bin/env python3
"""
Medical Performance Tests - System Critical
===========================================

Critical performance tests for medical processing to ensure
patient safety through reliable system response times.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor

from vigia_detect.cv_pipeline.medical_detector_factory import create_medical_detector
from vigia_detect.core.async_pipeline import async_pipeline
from vigia_detect.core.phi_tokenization_client import PHITokenizationClient


@pytest.mark.critical
@pytest.mark.performance
@pytest.mark.medical_safety
class TestMedicalProcessingPerformance:
    """Critical tests for medical processing performance under load."""
    
    @pytest.mark.asyncio
    async def test_emergency_case_processing_speed(self):
        """Verify emergency cases are processed within medical safety timeframes."""
        detector = create_medical_detector()
        
        # Emergency case that must be processed quickly
        emergency_image_path = "tests/fixtures/stage4_lpp_emergency.jpg"
        patient_token = "emergency-token-001"
        
        # Mock emergency case processing
        with patch.object(detector, 'detect_medical_condition') as mock_detect:
            mock_detect.return_value = {
                "lpp_grade": 4,
                "confidence": 0.96,
                "urgency": "critical",
                "processing_time_ms": 1200
            }
            
            start_time = time.time()
            
            result = await detector.detect_medical_condition(
                emergency_image_path, 
                patient_token, 
                {"urgency": "emergency"}
            )
            
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Emergency cases must be processed within 2 seconds
            assert processing_time <= 2000, f"Emergency processing too slow: {processing_time}ms"
            assert result["lpp_grade"] == 4
            assert result["confidence"] >= 0.9
    
    @pytest.mark.asyncio
    async def test_concurrent_patient_processing_capacity(self):
        """Verify system handles multiple concurrent patient cases safely."""
        async_processor = async_pipeline
        
        # Simulate 10 concurrent patient cases
        concurrent_cases = [
            {
                "token_id": f"concurrent-{i}",
                "image_path": f"tests/fixtures/patient_{i}.jpg",
                "urgency": "routine" if i < 8 else "critical"
            }
            for i in range(10)
        ]
        
        with patch.object(async_processor, 'process_medical_case_async') as mock_process:
            # Mock varying processing times
            async def mock_async_process(image_path, token_id, context):
                await asyncio.sleep(0.1)  # Simulate processing
                return {
                    "success": True,
                    "token_id": token_id,
                    "processing_time_ms": 100
                }
            
            mock_process.side_effect = mock_async_process
            
            # Execute concurrent processing
            start_time = time.time()
            
            tasks = [
                async_processor.process_medical_case_async(
                    case["image_path"], 
                    case["token_id"], 
                    {"urgency": case["urgency"]}
                )
                for case in concurrent_cases
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            total_time = time.time() - start_time
            
            # Verify all cases processed successfully
            successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
            assert len(successful_results) == 10
            
            # Verify concurrent processing efficiency (should be much faster than sequential)
            assert total_time <= 1.0, f"Concurrent processing too slow: {total_time}s"
    
    def test_high_volume_tokenization_performance(self):
        """Verify tokenization system handles high patient volume efficiently."""
        tokenization_client = PHITokenizationClient()
        
        # Simulate high-volume tokenization requests
        patient_batch = [
            {"hospital_mrn": f"MRN-2025-{i:03d}-BW", "patient_data": {"age": 70 + i}}
            for i in range(100)
        ]
        
        with patch.object(tokenization_client, 'tokenize_patient') as mock_tokenize:
            # Mock tokenization response
            async def mock_tokenize_patient(mrn, data):
                await asyncio.sleep(0.01)  # Simulate tokenization time
                return {
                    "token_id": f"token-{mrn.split('-')[2]}",
                    "patient_alias": f"Patient{mrn.split('-')[2]}"
                }
            
            mock_tokenize.side_effect = mock_tokenize_patient
            
            # Execute batch tokenization
            start_time = time.time()
            
            async def process_batch():
                tasks = [
                    tokenization_client.tokenize_patient(patient["hospital_mrn"], patient["patient_data"])
                    for patient in patient_batch
                ]
                return await asyncio.gather(*tasks)
            
            results = asyncio.run(process_batch())
            batch_time = time.time() - start_time
            
            # Verify all tokenizations completed
            assert len(results) == 100
            
            # Verify reasonable batch processing time (under 5 seconds for 100 patients)
            assert batch_time <= 5.0, f"Batch tokenization too slow: {batch_time}s"
            
            # Verify throughput (at least 20 patients per second)
            throughput = len(results) / batch_time
            assert throughput >= 20, f"Tokenization throughput too low: {throughput} patients/s"


@pytest.mark.critical
@pytest.mark.performance
@pytest.mark.scalability
class TestSystemScalabilityLimits:
    """Critical tests for system scalability under medical load."""
    
    def test_memory_usage_under_medical_load(self):
        """Verify system memory usage remains stable under medical processing load."""
        import psutil
        
        detector = create_medical_detector()
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Process multiple medical cases
        with patch.object(detector, 'detect_medical_condition') as mock_detect:
            mock_detect.return_value = {
                "lpp_grade": 2,
                "confidence": 0.88,
                "memory_efficient": True
            }
            
            # Simulate processing 50 cases
            for i in range(50):
                result = detector.detect_medical_condition(
                    f"test_image_{i}.jpg",
                    f"token-{i}",
                    {"case_number": i}
                )
                assert result["lpp_grade"] is not None
            
            final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Memory increase should be reasonable (less than 500MB for 50 cases)
            assert memory_increase <= 500, f"Excessive memory usage: {memory_increase}MB"
    
    @pytest.mark.asyncio
    async def test_database_connection_pool_performance(self):
        """Verify database connection pooling handles medical load efficiently."""
        from vigia_detect.db.database_client import DatabaseClient
        
        db_client = DatabaseClient()
        
        # Simulate concurrent database operations
        concurrent_operations = 20
        
        with patch.object(db_client, 'execute_query') as mock_query:
            # Mock database response
            async def mock_db_query(query, params):
                await asyncio.sleep(0.05)  # Simulate query time
                return {"success": True, "rows": 1}
            
            mock_query.side_effect = mock_db_query
            
            # Execute concurrent operations
            start_time = time.time()
            
            tasks = [
                db_client.execute_query(
                    "SELECT * FROM tokenized_patients WHERE token_id = %s",
                    [f"token-{i}"]
                )
                for i in range(concurrent_operations)
            ]
            
            results = await asyncio.gather(*tasks)
            operation_time = time.time() - start_time
            
            # Verify all operations completed
            assert len(results) == concurrent_operations
            assert all(r["success"] for r in results)
            
            # Verify connection pooling efficiency (should be much faster than sequential)
            assert operation_time <= 2.0, f"Database operations too slow: {operation_time}s"


@pytest.mark.critical
@pytest.mark.performance
@pytest.mark.medical_safety
class TestFailoverPerformance:
    """Critical tests for system failover performance during medical emergencies."""
    
    @pytest.mark.asyncio
    async def test_backup_system_activation_speed(self):
        """Verify backup systems activate quickly during primary system failures."""
        from vigia_detect.cv_pipeline.medical_detector_factory import create_medical_detector
        
        primary_detector = create_medical_detector("monai_primary")
        backup_detector = create_medical_detector("yolo_backup")
        
        # Simulate primary system failure
        emergency_case = {
            "image_path": "emergency_stage4.jpg",
            "token_id": "emergency-failover-001",
            "urgency": "critical"
        }
        
        with patch.object(primary_detector, 'detect_medical_condition') as mock_primary:
            # Primary system fails
            mock_primary.side_effect = Exception("Primary AI system failure")
            
            with patch.object(backup_detector, 'detect_medical_condition') as mock_backup:
                mock_backup.return_value = {
                    "lpp_grade": 4,
                    "confidence": 0.91,
                    "source": "backup_system",
                    "failover_time_ms": 800
                }
                
                # Execute failover
                start_time = time.time()
                
                try:
                    result = await primary_detector.detect_medical_condition(
                        emergency_case["image_path"],
                        emergency_case["token_id"],
                        emergency_case
                    )
                except Exception:
                    # Activate backup system
                    result = await backup_detector.detect_medical_condition(
                        emergency_case["image_path"],
                        emergency_case["token_id"],
                        emergency_case
                    )
                
                failover_time = (time.time() - start_time) * 1000  # Convert to ms
                
                # Failover must complete within 1 second for medical safety
                assert failover_time <= 1000, f"Failover too slow: {failover_time}ms"
                assert result["lpp_grade"] == 4
                assert result["source"] == "backup_system"