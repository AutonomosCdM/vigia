"""
Specific E2E tests for detection pipeline critical flows.
Tests the core medical detection workflow step by step.
"""
import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any
import numpy as np

from vigia_detect.core.unified_image_processor import UnifiedImageProcessor
from vigia_detect.cv_pipeline.detector import YOLODetector
from vigia_detect.cv_pipeline.preprocessor import ImagePreprocessor
from vigia_detect.core.constants import LPPGrade, LPP_SEVERITY_ALERTS
from vigia_detect.utils.error_handling import ImageProcessingError, DetectionError
from tests.shared_fixtures import (
    sample_image_path,
    mock_detection_result,
    SAMPLE_PATIENT_CODES
)


class TestDetectionPipelineCritical:
    """Test critical detection pipeline flows step by step."""
    
    @pytest.fixture
    def processor(self):
        """Create image processor for testing."""
        return UnifiedImageProcessor()
    
    @pytest.fixture
    def mock_yolo_detector(self):
        """Create mock YOLO detector with predictable responses."""
        detector = Mock(spec=YOLODetector)
        
        # Default successful detection
        detector.detect.return_value = {
            'detections': [
                {
                    'class': 'lpp_grade_2',
                    'confidence': 0.85,
                    'bbox': [100, 100, 200, 200],
                    'area': 10000,
                    'center': [150, 150]
                }
            ],
            'processing_time': 0.5,
            'model_version': 'yolov5-medical-v1.0',
            'image_size': [640, 640]
        }
        
        detector.load_model.return_value = True
        detector.is_model_loaded.return_value = True
        
        return detector
    
    @pytest.fixture
    def mock_preprocessor(self):
        """Create mock image preprocessor."""
        preprocessor = Mock(spec=ImagePreprocessor)
        
        # Mock successful preprocessing
        preprocessor.preprocess.return_value = {
            'processed_image': np.zeros((640, 640, 3), dtype=np.uint8),
            'original_size': (1024, 768),
            'scale_factor': 0.625,
            'padding': [0, 96, 0, 96],
            'preprocessing_time': 0.1
        }
        
        preprocessor.validate_image.return_value = {
            'valid': True,
            'format': 'JPEG',
            'size': (1024, 768),
            'channels': 3
        }
        
        return preprocessor

    @pytest.mark.asyncio
    async def test_complete_detection_workflow(self, processor, mock_yolo_detector, mock_preprocessor, sample_image_path):
        """
        CRITICAL: Test complete detection workflow from raw image to medical assessment.
        This tests the entire pipeline that medical staff rely on.
        """
        patient_code = SAMPLE_PATIENT_CODES[0]
        
        with patch('vigia_detect.cv_pipeline.detector.YOLODetector', return_value=mock_yolo_detector):
            with patch('vigia_detect.cv_pipeline.preprocessor.ImagePreprocessor', return_value=mock_preprocessor):
                
                # Process image through complete pipeline
                result = processor.process_single_image(
                    image_path=str(sample_image_path),
                    patient_code=patient_code,
                    save_visualization=True
                )
                
                # Validate pipeline execution
                assert result['success'] is True
                assert 'detection_result' in result
                assert 'medical_assessment' in result
                assert 'processing_metadata' in result
                
                # Validate detection result structure
                detection = result['detection_result']
                assert 'detections' in detection
                assert 'processing_time' in detection
                assert len(detection['detections']) > 0
                
                # Validate medical assessment
                assessment = result['medical_assessment']
                assert 'lpp_grade' in assessment
                assert 'severity_level' in assessment
                assert 'recommendations' in assessment
                assert 'confidence_score' in assessment
                assert 'risk_factors' in assessment
                
                # Validate LPP grade is correctly determined
                detected_class = detection['detections'][0]['class']
                expected_grade = int(detected_class.split('_')[-1])
                assert assessment['lpp_grade'] == expected_grade
                
                # Validate severity mapping
                expected_severity = LPP_SEVERITY_ALERTS[expected_grade]['level']
                assert assessment['severity_level'] == expected_severity
                
                # Validate recommendations are appropriate for grade
                recommendations = assessment['recommendations']
                assert isinstance(recommendations, list)
                assert len(recommendations) > 0
                
                # For grade 2, should include specific treatments
                if expected_grade == 2:
                    rec_text = ' '.join(recommendations).lower()
                    assert any(keyword in rec_text for keyword in ['curación', 'apósito', 'protocolo'])

    @pytest.mark.asyncio
    async def test_multi_detection_handling(self, processor, mock_yolo_detector, mock_preprocessor, sample_image_path):
        """
        CRITICAL: Test handling of multiple LPP detections in single image.
        Medical staff need to see all lesions detected.
        """
        # Configure mock to return multiple detections
        mock_yolo_detector.detect.return_value = {
            'detections': [
                {
                    'class': 'lpp_grade_1',
                    'confidence': 0.75,
                    'bbox': [50, 50, 150, 150],
                    'area': 10000,
                    'center': [100, 100]
                },
                {
                    'class': 'lpp_grade_2',
                    'confidence': 0.85,
                    'bbox': [300, 300, 400, 400],
                    'area': 10000,
                    'center': [350, 350]
                },
                {
                    'class': 'lpp_grade_3',
                    'confidence': 0.90,
                    'bbox': [200, 200, 300, 300],
                    'area': 10000,
                    'center': [250, 250]
                }
            ],
            'processing_time': 0.8,
            'model_version': 'yolov5-medical-v1.0'
        }
        
        with patch('vigia_detect.cv_pipeline.detector.YOLODetector', return_value=mock_yolo_detector):
            with patch('vigia_detect.cv_pipeline.preprocessor.ImagePreprocessor', return_value=mock_preprocessor):
                
                result = processor.process_single_image(
                    image_path=str(sample_image_path),
                    patient_code=SAMPLE_PATIENT_CODES[0]
                )
                
                # Validate all detections are captured
                detections = result['detection_result']['detections']
                assert len(detections) == 3
                
                # Validate grades are correctly extracted
                detected_grades = [int(d['class'].split('_')[-1]) for d in detections]
                assert set(detected_grades) == {1, 2, 3}
                
                # Validate medical assessment accounts for highest grade
                assessment = result['medical_assessment']
                assert assessment['lpp_grade'] == 3  # Should be highest detected grade
                assert assessment['severity_level'] == 'URGENTE'  # Grade 3 severity
                
                # Validate multiple lesions are reported
                assert 'lesion_count' in assessment
                assert assessment['lesion_count'] == 3
                
                # Validate recommendations address highest severity
                recommendations = ' '.join(assessment['recommendations']).lower()
                assert any(keyword in recommendations for keyword in ['urgente', 'médica', 'desbridamiento'])

    @pytest.mark.asyncio
    async def test_confidence_threshold_filtering(self, processor, mock_yolo_detector, mock_preprocessor, sample_image_path):
        """
        CRITICAL: Test that low-confidence detections are filtered appropriately.
        Medical systems must not report uncertain findings as definitive.
        """
        # Configure mock with mixed confidence detections
        mock_yolo_detector.detect.return_value = {
            'detections': [
                {
                    'class': 'lpp_grade_2',
                    'confidence': 0.95,  # High confidence - should be included
                    'bbox': [100, 100, 200, 200],
                    'area': 10000
                },
                {
                    'class': 'lpp_grade_3',
                    'confidence': 0.45,  # Low confidence - should be filtered or flagged
                    'bbox': [300, 300, 400, 400],
                    'area': 10000
                },
                {
                    'class': 'lpp_grade_1',
                    'confidence': 0.75,  # Medium confidence - should be included with note
                    'bbox': [200, 200, 300, 300],
                    'area': 10000
                }
            ],
            'processing_time': 0.6
        }
        
        with patch('vigia_detect.cv_pipeline.detector.YOLODetector', return_value=mock_yolo_detector):
            with patch('vigia_detect.cv_pipeline.preprocessor.ImagePreprocessor', return_value=mock_preprocessor):
                
                result = processor.process_single_image(
                    image_path=str(sample_image_path),
                    patient_code=SAMPLE_PATIENT_CODES[0]
                )
                
                # Validate confidence filtering
                assessment = result['medical_assessment']
                
                # High-confidence detection should be primary
                assert assessment['lpp_grade'] == 2  # Highest confidence high-grade detection
                assert assessment['confidence_score'] >= 0.95
                
                # Low-confidence detections should be handled appropriately
                if 'uncertain_findings' in assessment:
                    uncertain = assessment['uncertain_findings']
                    assert len(uncertain) > 0
                    
                    # Find the low-confidence grade 3 detection
                    grade_3_uncertain = [u for u in uncertain if u.get('grade') == 3]
                    assert len(grade_3_uncertain) > 0
                    assert grade_3_uncertain[0]['confidence'] == 0.45
                
                # Validate recommendations mention uncertainty for low-confidence findings
                recommendations = ' '.join(assessment['recommendations']).lower()
                if assessment.get('uncertain_findings'):
                    assert any(keyword in recommendations for keyword in ['evaluar', 'confirmar', 'revisar'])

    @pytest.mark.asyncio
    async def test_preprocessing_error_handling(self, processor, mock_yolo_detector, mock_preprocessor):
        """
        CRITICAL: Test preprocessing error handling doesn't crash the system.
        Medical systems must handle corrupted or invalid images gracefully.
        """
        # Configure preprocessor to fail
        mock_preprocessor.validate_image.return_value = {
            'valid': False,
            'error': 'Corrupted image file'
        }
        
        with patch('vigia_detect.cv_pipeline.detector.YOLODetector', return_value=mock_yolo_detector):
            with patch('vigia_detect.cv_pipeline.preprocessor.ImagePreprocessor', return_value=mock_preprocessor):
                
                # Should raise ImageProcessingError, not crash
                with pytest.raises(ImageProcessingError) as exc_info:
                    processor.process_single_image(
                        image_path="corrupted_image.jpg",
                        patient_code=SAMPLE_PATIENT_CODES[0]
                    )
                
                error = exc_info.value
                assert error.category.value == "processing"
                assert "corrupted" in error.user_message.lower()
                assert len(error.recovery_suggestions) > 0
                
                # Recovery suggestions should be medical-appropriate
                suggestions = ' '.join(error.recovery_suggestions).lower()
                assert any(keyword in suggestions for keyword in ['imagen', 'archivo', 'formato'])

    @pytest.mark.asyncio
    async def test_yolo_model_failure_handling(self, processor, mock_yolo_detector, mock_preprocessor, sample_image_path):
        """
        CRITICAL: Test YOLO model failure handling.
        Medical systems must handle AI model failures gracefully.
        """
        # Configure YOLO to fail
        mock_yolo_detector.detect.side_effect = Exception("YOLO model inference failed")
        
        with patch('vigia_detect.cv_pipeline.detector.YOLODetector', return_value=mock_yolo_detector):
            with patch('vigia_detect.cv_pipeline.preprocessor.ImagePreprocessor', return_value=mock_preprocessor):
                
                # Should raise DetectionError
                with pytest.raises(DetectionError) as exc_info:
                    processor.process_single_image(
                        image_path=str(sample_image_path),
                        patient_code=SAMPLE_PATIENT_CODES[0]
                    )
                
                error = exc_info.value
                assert error.category.value == "processing"
                assert "modelo" in error.user_message.lower() or "model" in error.user_message.lower()
                
                # Should suggest manual review
                suggestions = ' '.join(error.recovery_suggestions).lower()
                assert any(keyword in suggestions for keyword in ['manual', 'técnico', 'modelo'])

    @pytest.mark.asyncio
    async def test_edge_case_no_detections(self, processor, mock_yolo_detector, mock_preprocessor, sample_image_path):
        """
        CRITICAL: Test handling when no LPP is detected.
        Medical systems must clearly communicate negative results.
        """
        # Configure YOLO to return no detections
        mock_yolo_detector.detect.return_value = {
            'detections': [],
            'processing_time': 0.3,
            'model_version': 'yolov5-medical-v1.0'
        }
        
        with patch('vigia_detect.cv_pipeline.detector.YOLODetector', return_value=mock_yolo_detector):
            with patch('vigia_detect.cv_pipeline.preprocessor.ImagePreprocessor', return_value=mock_preprocessor):
                
                result = processor.process_single_image(
                    image_path=str(sample_image_path),
                    patient_code=SAMPLE_PATIENT_CODES[0]
                )
                
                # Validate negative result handling
                assert result['success'] is True
                
                detection = result['detection_result']
                assert len(detection['detections']) == 0
                
                assessment = result['medical_assessment']
                assert assessment['lpp_grade'] == 0  # No lesion
                assert assessment['severity_level'] == 'INFO'
                assert assessment['confidence_score'] == 1.0  # Confident no detection
                
                # Validate appropriate recommendations for no detection
                recommendations = ' '.join(assessment['recommendations']).lower()
                assert any(keyword in recommendations for keyword in ['preventivo', 'vigilancia', 'cambios'])

    @pytest.mark.asyncio
    async def test_visualization_generation(self, processor, mock_yolo_detector, mock_preprocessor, sample_image_path):
        """
        CRITICAL: Test medical visualization generation.
        Medical staff need visual confirmation of detections.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            with patch('vigia_detect.cv_pipeline.detector.YOLODetector', return_value=mock_yolo_detector):
                with patch('vigia_detect.cv_pipeline.preprocessor.ImagePreprocessor', return_value=mock_preprocessor):
                    
                    result = processor.process_single_image(
                        image_path=str(sample_image_path),
                        patient_code=SAMPLE_PATIENT_CODES[0],
                        save_visualization=True,
                        output_dir=str(output_dir)
                    )
                    
                    # Validate visualization was created
                    assert 'visualization_path' in result
                    
                    viz_path = Path(result['visualization_path'])
                    assert viz_path.exists()
                    assert viz_path.suffix.lower() in ['.jpg', '.jpeg', '.png']
                    
                    # Validate filename includes patient code for medical tracking
                    assert SAMPLE_PATIENT_CODES[0].replace('-', '_') in viz_path.name

    @pytest.mark.asyncio
    async def test_medical_metadata_tracking(self, processor, mock_yolo_detector, mock_preprocessor, sample_image_path):
        """
        CRITICAL: Test medical metadata is properly tracked.
        Medical systems need complete audit trails.
        """
        custom_metadata = {
            'medical_professional': 'Dr. Smith',
            'examination_date': '2025-01-15',
            'anatomical_region': 'sacro',
            'patient_position': 'lateral_decubitus'
        }
        
        with patch('vigia_detect.cv_pipeline.detector.YOLODetector', return_value=mock_yolo_detector):
            with patch('vigia_detect.cv_pipeline.preprocessor.ImagePreprocessor', return_value=mock_preprocessor):
                
                result = processor.process_single_image(
                    image_path=str(sample_image_path),
                    patient_code=SAMPLE_PATIENT_CODES[0],
                    metadata=custom_metadata
                )
                
                # Validate metadata is preserved and augmented
                metadata = result['processing_metadata']
                
                # Custom metadata should be preserved
                for key, value in custom_metadata.items():
                    assert metadata.get(key) == value
                
                # System metadata should be added
                assert 'processing_timestamp' in metadata
                assert 'model_version' in metadata
                assert 'vigia_version' in metadata
                assert 'patient_code' in metadata
                
                # Medical compliance metadata
                assert 'data_retention_date' in metadata
                assert 'processing_location' in metadata

    @pytest.mark.asyncio  
    async def test_batch_processing_consistency(self, processor, mock_yolo_detector, mock_preprocessor, sample_image_path):
        """
        CRITICAL: Test that batch processing maintains consistency.
        Medical systems must produce consistent results across processing modes.
        """
        patient_code = SAMPLE_PATIENT_CODES[0]
        
        with patch('vigia_detect.cv_pipeline.detector.YOLODetector', return_value=mock_yolo_detector):
            with patch('vigia_detect.cv_pipeline.preprocessor.ImagePreprocessor', return_value=mock_preprocessor):
                
                # Process same image multiple times
                results = []
                for i in range(3):
                    result = processor.process_single_image(
                        image_path=str(sample_image_path),
                        patient_code=patient_code
                    )
                    results.append(result)
                
                # Validate consistency across runs
                base_assessment = results[0]['medical_assessment']
                
                for result in results[1:]:
                    assessment = result['medical_assessment']
                    
                    # Core medical findings should be identical
                    assert assessment['lpp_grade'] == base_assessment['lpp_grade']
                    assert assessment['severity_level'] == base_assessment['severity_level']
                    assert assessment['confidence_score'] == base_assessment['confidence_score']
                    
                    # Recommendations should be consistent
                    assert len(assessment['recommendations']) == len(base_assessment['recommendations'])
                
                # Validate processing times are reasonable and consistent
                processing_times = [r['detection_result']['processing_time'] for r in results]
                avg_time = sum(processing_times) / len(processing_times)
                
                # No processing should take more than 2x average (performance consistency)
                for time_taken in processing_times:
                    assert time_taken <= avg_time * 2.0, f"Processing time inconsistency: {time_taken} vs avg {avg_time}"