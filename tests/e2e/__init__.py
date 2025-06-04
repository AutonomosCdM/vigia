"""
End-to-End tests for Vigia Medical Detection System.

This package contains comprehensive E2E tests for validating the complete
system functionality after major refactoring.

Test Modules:
- test_critical_medical_flows: Core medical functionality tests
- test_detection_pipeline: Specific detection pipeline tests
- test_regression_flows: Regression tests for existing functionality

Usage:
    # Run all E2E tests
    pytest tests/e2e/
    
    # Run only critical medical flows
    pytest tests/e2e/test_critical_medical_flows.py
    
    # Run with verbose output
    pytest tests/e2e/ -v
    
    # Run specific test class
    pytest tests/e2e/test_detection_pipeline.py::TestDetectionPipelineCritical
"""

# Test configuration
import pytest

# Mark all tests in this package as E2E tests
pytestmark = pytest.mark.e2e