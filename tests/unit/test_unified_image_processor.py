"""
Tests for the unified image processor.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from vigia_detect.core.unified_image_processor import UnifiedImageProcessor
from tests.shared_fixtures import (
    sample_image_path,
    sample_patient_code,
    mock_detector,
    mock_preprocessor,
    test_data_factory,
    assert_detection_result_structure
)


class TestUnifiedImageProcessor:
    
    @patch('vigia_detect.core.unified_image_processor.Detector')
    @patch('vigia_detect.core.unified_image_processor.Preprocessor')
    def test_initialization(self, mock_preprocessor_class, mock_detector_class):
        """Test processor initialization"""
        processor = UnifiedImageProcessor()
        
        assert processor.service_name == "UnifiedImageProcessor"
        mock_detector_class.assert_called_once()
        mock_preprocessor_class.assert_called_once()
    
    @patch('vigia_detect.core.unified_image_processor.Detector')
    @patch('vigia_detect.core.unified_image_processor.Preprocessor')
    def test_validate_connection(self, mock_preprocessor_class, mock_detector_class):
        """Test connection validation"""
        processor = UnifiedImageProcessor()
        
        # Should return True when both detector and preprocessor are initialized
        assert processor.validate_connection() is True
        
        # Should return False if detector is None
        processor.detector = None
        assert processor.validate_connection() is False
    
    @patch('vigia_detect.core.unified_image_processor.is_valid_image')
    @patch('vigia_detect.core.unified_image_processor.Detector')
    @patch('vigia_detect.core.unified_image_processor.Preprocessor')
    def test_process_single_image_success(self, mock_preprocessor_class, mock_detector_class, mock_is_valid):
        """Test successful single image processing"""
        # Setup mocks
        mock_is_valid.return_value = True
        
        mock_detector = Mock()
        mock_detector.detect.return_value = {
            "detections": [{"bbox": [10, 10, 50, 50], "confidence": 0.9, "grade": 2}],
            "confidence_scores": [0.9]
        }
        mock_detector_class.return_value = mock_detector
        
        mock_preprocessor = Mock()
        mock_preprocessor.preprocess.return_value = "processed_image"
        mock_preprocessor.get_original_size.return_value = (1920, 1080)
        mock_preprocessor.get_applied_steps.return_value = ["resize", "normalize"]
        mock_preprocessor_class.return_value = mock_preprocessor
        
        # Test
        processor = UnifiedImageProcessor()
        result = processor.process_single_image(
            image_path="/test/image.jpg",
            patient_code="CD-2025-001"
        )
        
        # Assertions
        assert result["success"] is True
        assert "processing_id" in result
        assert "processing_time_seconds" in result
        assert result["patient_code"] == "CD-2025-001"
        assert "results" in result
        
        # Check detection results structure
        detection_results = result["results"]["detections"][0]
        assert_detection_result_structure(detection_results)
    
    @patch('vigia_detect.core.unified_image_processor.is_valid_image')
    @patch('vigia_detect.core.unified_image_processor.Detector')
    @patch('vigia_detect.core.unified_image_processor.Preprocessor')
    def test_process_single_image_invalid_file(self, mock_preprocessor_class, mock_detector_class, mock_is_valid):
        """Test processing with invalid image file"""
        mock_is_valid.return_value = False
        
        processor = UnifiedImageProcessor()
        result = processor.process_single_image("/invalid/image.txt")
        
        assert result["success"] is False
        assert "Invalid image file" in result["error"]
    
    @patch('vigia_detect.core.unified_image_processor.is_valid_image')
    @patch('vigia_detect.core.unified_image_processor.Detector')
    @patch('vigia_detect.core.unified_image_processor.Preprocessor')
    def test_process_multiple_images(self, mock_preprocessor_class, mock_detector_class, mock_is_valid):
        """Test batch processing of multiple images"""
        # Setup mocks
        mock_is_valid.return_value = True
        
        mock_detector = Mock()
        mock_detector.detect.return_value = {
            "detections": [{"bbox": [10, 10, 50, 50], "confidence": 0.8, "grade": 1}],
            "confidence_scores": [0.8]
        }
        mock_detector_class.return_value = mock_detector
        
        mock_preprocessor = Mock()
        mock_preprocessor.preprocess.return_value = "processed_image"
        mock_preprocessor.get_original_size.return_value = (1920, 1080)
        mock_preprocessor.get_applied_steps.return_value = ["resize"]
        mock_preprocessor_class.return_value = mock_preprocessor
        
        # Test
        processor = UnifiedImageProcessor()
        image_paths = ["/test/image1.jpg", "/test/image2.jpg"]
        result = processor.process_multiple_images(
            image_paths=image_paths,
            patient_code="CD-2025-001"
        )
        
        # Assertions
        assert "batch_id" in result
        assert result["total_images"] == 2
        assert result["successful_count"] == 2
        assert result["failed_count"] == 0
        assert len(result["results"]) == 2
    
    @patch('vigia_detect.core.unified_image_processor.Detector')
    @patch('vigia_detect.core.unified_image_processor.Preprocessor')
    def test_medical_assessment_no_lesions(self, mock_preprocessor_class, mock_detector_class):
        """Test medical assessment when no lesions are detected"""
        processor = UnifiedImageProcessor()
        
        detection_results = {"detections": [], "confidence_scores": []}
        assessment = processor._create_medical_assessment(detection_results)
        
        assert assessment["status"] == "no_lesions_detected"
        assert assessment["grade"] == 0
        assert "No se detectaron lesiones" in assessment["description"]
    
    @patch('vigia_detect.core.unified_image_processor.Detector')
    @patch('vigia_detect.core.unified_image_processor.Preprocessor')
    def test_medical_assessment_with_lesions(self, mock_preprocessor_class, mock_detector_class):
        """Test medical assessment when lesions are detected"""
        processor = UnifiedImageProcessor()
        
        detection_results = {
            "detections": [
                {"grade": 2}, 
                {"grade": 1}
            ],
            "confidence_scores": [0.9, 0.7]
        }
        assessment = processor._create_medical_assessment(detection_results)
        
        assert assessment["status"] == "lesions_detected"
        assert assessment["highest_grade"] == 2
        assert assessment["total_detections"] == 2
    
    @patch('vigia_detect.core.unified_image_processor.Detector')
    @patch('vigia_detect.core.unified_image_processor.Preprocessor')
    def test_severity_determination(self, mock_preprocessor_class, mock_detector_class):
        """Test severity level determination"""
        processor = UnifiedImageProcessor()
        
        # Test high severity (grade 3+)
        high_severity_results = {"detections": [{"grade": 3}]}
        assert processor._determine_severity_level(high_severity_results) == "high"
        
        # Test medium severity (grade 2)
        medium_severity_results = {"detections": [{"grade": 2}]}
        assert processor._determine_severity_level(medium_severity_results) == "medium"
        
        # Test low severity (grade 1)
        low_severity_results = {"detections": [{"grade": 1}]}
        assert processor._determine_severity_level(low_severity_results) == "low"
        
        # Test no severity (no detections)
        no_severity_results = {"detections": []}
        assert processor._determine_severity_level(no_severity_results) == "none"
    
    @patch('vigia_detect.core.unified_image_processor.Detector')
    @patch('vigia_detect.core.unified_image_processor.Preprocessor')
    def test_medical_attention_required(self, mock_preprocessor_class, mock_detector_class):
        """Test medical attention requirement determination"""
        processor = UnifiedImageProcessor()
        
        # Grade 2+ requires medical attention
        grade2_results = {"detections": [{"grade": 2}]}
        assert processor._requires_medical_attention(grade2_results) is True
        
        # Grade 1 doesn't require immediate medical attention
        grade1_results = {"detections": [{"grade": 1}]}
        assert processor._requires_medical_attention(grade1_results) is False
        
        # No detections don't require medical attention
        no_detections = {"detections": []}
        assert processor._requires_medical_attention(no_detections) is False
    
    @patch('vigia_detect.core.unified_image_processor.Detector')
    @patch('vigia_detect.core.unified_image_processor.Preprocessor')
    def test_recommendations_generation(self, mock_preprocessor_class, mock_detector_class):
        """Test recommendation generation based on detection grade"""
        processor = UnifiedImageProcessor()
        
        # Test grade 1 recommendations
        grade1_results = {"detections": [{"grade": 1}]}
        recommendations = processor._generate_recommendations(grade1_results)
        assert "Alivio de presión inmediato" in recommendations
        
        # Test grade 2 recommendations
        grade2_results = {"detections": [{"grade": 2}]}
        recommendations = processor._generate_recommendations(grade2_results)
        assert "Evaluación médica urgente" in recommendations
        
        # Test no detection recommendations
        no_detections = {"detections": []}
        recommendations = processor._generate_recommendations(no_detections)
        assert "medidas preventivas" in recommendations[0].lower()
    
    @patch('vigia_detect.core.unified_image_processor.Detector')
    @patch('vigia_detect.core.unified_image_processor.Preprocessor')
    def test_error_result_creation(self, mock_preprocessor_class, mock_detector_class):
        """Test error result creation"""
        processor = UnifiedImageProcessor()
        
        error_result = processor._create_error_result(
            "Test error",
            "/test/image.jpg",
            "test-123"
        )
        
        assert error_result["success"] is False
        assert error_result["error"] == "Test error"
        assert error_result["image_path"] == "/test/image.jpg"
        assert error_result["processing_id"] == "test-123"
        assert "timestamp" in error_result