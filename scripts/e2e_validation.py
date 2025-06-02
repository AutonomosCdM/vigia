#!/usr/bin/env python3
"""
E2E validation script for Vigia clinical workflow.
Tests the complete pipeline: WhatsApp → Image → Diagnosis → Validation → Storage
"""

import os
import sys
import time
import json
import requests
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('vigia-e2e-validation')

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

try:
    from vigia_detect.cv_pipeline.detector import PressureInjuryDetector
    from vigia_detect.db.supabase_client import SupabaseClient
    from vigia_detect.webhook.client import WebhookClient
    from vigia_detect.messaging.slack_notifier import SlackNotifier
    from vigia_detect.utils.image_utils import load_image, validate_image
except ImportError as e:
    logger.error(f"Failed to import Vigia modules: {e}")
    sys.exit(1)


class E2EValidator:
    """End-to-end validation for Vigia clinical workflow."""
    
    def __init__(self):
        """Initialize E2E validator."""
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "tests": {},
            "overall_status": "unknown",
            "errors": []
        }
        
        # Initialize services
        self.detector = None
        self.db_client = None
        self.webhook_client = None
        self.slack_notifier = None
        
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize all required services."""
        try:
            self.detector = PressureInjuryDetector()
            logger.info("✓ Detector initialized")
        except Exception as e:
            logger.error(f"✗ Failed to initialize detector: {e}")
            self.results["errors"].append(f"Detector initialization: {e}")
        
        try:
            self.db_client = SupabaseClient()
            logger.info("✓ Database client initialized")
        except Exception as e:
            logger.error(f"✗ Failed to initialize database: {e}")
            self.results["errors"].append(f"Database initialization: {e}")
        
        try:
            webhook_url = os.getenv('WEBHOOK_URL', 'http://localhost:8001/webhook')
            self.webhook_client = WebhookClient(
                webhook_url=webhook_url,
                api_key=os.getenv('WEBHOOK_API_KEY')
            )
            logger.info("✓ Webhook client initialized")
        except Exception as e:
            logger.error(f"✗ Failed to initialize webhook client: {e}")
            self.results["errors"].append(f"Webhook initialization: {e}")
        
        try:
            self.slack_notifier = SlackNotifier()
            logger.info("✓ Slack notifier initialized")
        except Exception as e:
            logger.error(f"✗ Failed to initialize Slack notifier: {e}")
            self.results["errors"].append(f"Slack initialization: {e}")
    
    def test_image_processing(self, image_path: str) -> Dict[str, Any]:
        """
        Test image processing pipeline.
        
        Args:
            image_path: Path to test image
            
        Returns:
            Test results
        """
        logger.info(f"Testing image processing with {image_path}")
        result = {"status": "failed", "details": {}}
        
        try:
            # 1. Load and validate image
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Test image not found: {image_path}")
            
            image = load_image(image_path)
            is_valid, validation_msg = validate_image(image)
            
            if not is_valid:
                raise ValueError(f"Invalid image: {validation_msg}")
            
            result["details"]["image_loaded"] = True
            logger.info("✓ Image loaded and validated")
            
            # 2. Run detection
            if self.detector:
                detection_result = self.detector.detect(image_path)
                result["details"]["detection"] = detection_result
                result["details"]["detection_success"] = True
                logger.info("✓ Detection completed")
            else:
                raise ValueError("Detector not available")
            
            # 3. Store results in database
            if self.db_client:
                patient_data = {
                    "patient_code": f"E2E-TEST-{int(time.time())}",
                    "detection_results": detection_result,
                    "image_path": image_path,
                    "test_run": True
                }
                
                db_result = self.db_client.insert_detection(patient_data)
                result["details"]["database_storage"] = db_result
                result["details"]["storage_success"] = True
                logger.info("✓ Results stored in database")
            else:
                logger.warning("⚠ Database client not available, skipping storage")
            
            # 4. Send webhook notification
            if self.webhook_client:
                webhook_payload = {
                    "event_type": "detection.completed",
                    "payload": {
                        "patient_code": patient_data.get("patient_code"),
                        "detection": detection_result,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
                
                webhook_result = self.webhook_client.send_async(webhook_payload)
                result["details"]["webhook"] = webhook_result
                result["details"]["webhook_success"] = True
                logger.info("✓ Webhook notification sent")
            else:
                logger.warning("⚠ Webhook client not available, skipping notification")
            
            # 5. Send Slack notification
            if self.slack_notifier:
                slack_message = f"""🧪 E2E Test Completed
                
📊 Detection Results:
{json.dumps(detection_result, indent=2)}

⏰ Timestamp: {datetime.utcnow().isoformat()}
🧬 Patient Code: {patient_data.get('patient_code')}
"""
                
                slack_result = self.slack_notifier.send_notification(
                    message=slack_message,
                    channel="vigia-e2e-tests"
                )
                result["details"]["slack"] = slack_result
                result["details"]["slack_success"] = True
                logger.info("✓ Slack notification sent")
            else:
                logger.warning("⚠ Slack notifier not available, skipping notification")
            
            result["status"] = "success"
            
        except Exception as e:
            logger.error(f"✗ Image processing test failed: {e}")
            result["details"]["error"] = str(e)
            self.results["errors"].append(f"Image processing: {e}")
        
        return result
    
    def test_webhook_server(self) -> Dict[str, Any]:
        """Test webhook server health and functionality."""
        logger.info("Testing webhook server")
        result = {"status": "failed", "details": {}}
        
        try:
            webhook_url = os.getenv('WEBHOOK_URL', 'http://localhost:8001')
            
            # Test health endpoint
            health_response = requests.get(f"{webhook_url}/health", timeout=10)
            if health_response.status_code == 200:
                result["details"]["health_check"] = health_response.json()
                result["details"]["health_success"] = True
                logger.info("✓ Webhook server health check passed")
            else:
                raise Exception(f"Health check failed: {health_response.status_code}")
            
            # Test events endpoint
            events_response = requests.get(f"{webhook_url}/webhook/events", timeout=10)
            if events_response.status_code == 200:
                result["details"]["events"] = events_response.json()
                result["details"]["events_success"] = True
                logger.info("✓ Webhook events endpoint accessible")
            else:
                logger.warning(f"⚠ Events endpoint failed: {events_response.status_code}")
            
            result["status"] = "success"
            
        except requests.exceptions.ConnectionError:
            logger.error("✗ Webhook server not reachable")
            result["details"]["error"] = "Server not reachable"
        except Exception as e:
            logger.error(f"✗ Webhook server test failed: {e}")
            result["details"]["error"] = str(e)
            self.results["errors"].append(f"Webhook server: {e}")
        
        return result
    
    def test_whatsapp_server(self) -> Dict[str, Any]:
        """Test WhatsApp server health."""
        logger.info("Testing WhatsApp server")
        result = {"status": "failed", "details": {}}
        
        try:
            whatsapp_url = os.getenv('WHATSAPP_SERVER_URL', 'http://localhost:5001')
            
            # Test health endpoint
            health_response = requests.get(f"{whatsapp_url}/health", timeout=10)
            if health_response.status_code == 200:
                result["details"]["health_check"] = health_response.json()
                result["details"]["health_success"] = True
                logger.info("✓ WhatsApp server health check passed")
            else:
                raise Exception(f"Health check failed: {health_response.status_code}")
            
            result["status"] = "success"
            
        except requests.exceptions.ConnectionError:
            logger.error("✗ WhatsApp server not reachable")
            result["details"]["error"] = "Server not reachable"
        except Exception as e:
            logger.error(f"✗ WhatsApp server test failed: {e}")
            result["details"]["error"] = str(e)
            self.results["errors"].append(f"WhatsApp server: {e}")
        
        return result
    
    def run_validation(self, test_image_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Run complete E2E validation.
        
        Args:
            test_image_path: Optional path to test image
            
        Returns:
            Complete validation results
        """
        logger.info("Starting E2E validation")
        
        # Use default test image if none provided
        if not test_image_path:
            test_image_path = str(Path(__file__).parent.parent / "vigia_detect/cv_pipeline/tests/data/test_eritema_simple.jpg")
        
        # Run all tests
        tests = {
            "image_processing": self.test_image_processing(test_image_path),
            "webhook_server": self.test_webhook_server(),
            "whatsapp_server": self.test_whatsapp_server()
        }
        
        self.results["tests"] = tests
        
        # Determine overall status
        failed_tests = [name for name, result in tests.items() if result["status"] == "failed"]
        
        if not failed_tests:
            self.results["overall_status"] = "success"
            logger.info("🎉 All E2E tests passed!")
        else:
            self.results["overall_status"] = "partial_failure"
            logger.warning(f"⚠ Some tests failed: {failed_tests}")
        
        # Save results
        self._save_results()
        
        return self.results
    
    def _save_results(self):
        """Save validation results to file."""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        results_file = Path(__file__).parent.parent / f"e2e_validation_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Results saved to: {results_file}")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run E2E validation for Vigia")
    parser.add_argument("--image", help="Path to test image")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    validator = E2EValidator()
    results = validator.run_validation(args.image)
    
    # Print summary
    print("\n" + "="*50)
    print("E2E VALIDATION SUMMARY")
    print("="*50)
    print(f"Overall Status: {results['overall_status'].upper()}")
    print(f"Timestamp: {results['timestamp']}")
    print(f"Errors: {len(results['errors'])}")
    
    for test_name, test_result in results['tests'].items():
        status_icon = "✓" if test_result['status'] == 'success' else "✗"
        print(f"{status_icon} {test_name}: {test_result['status']}")
    
    if results['errors']:
        print("\nErrors:")
        for error in results['errors']:
            print(f"  - {error}")
    
    print("="*50)
    
    # Exit with appropriate code
    sys.exit(0 if results['overall_status'] == 'success' else 1)


if __name__ == "__main__":
    main()