#!/usr/bin/env python3
"""
Simulate WhatsApp flow for Clinical Dry Run.
This script simulates sending images via WhatsApp webhook to test the complete flow.
"""

import os
import sys
import time
import json
import requests
import base64
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('whatsapp-simulator')


class WhatsAppSimulator:
    """Simulates WhatsApp messages for testing."""
    
    def __init__(self, webhook_url: str = "http://localhost:5005/webhook/whatsapp"):
        """
        Initialize WhatsApp simulator.
        
        Args:
            webhook_url: URL of the WhatsApp webhook endpoint
        """
        self.webhook_url = webhook_url
        self.test_phone = "+1234567890"  # Simulated phone number
        
    def send_text_message(self, text: str, from_number: Optional[str] = None) -> Dict[str, Any]:
        """
        Simulate sending a text message.
        
        Args:
            text: Message text
            from_number: Sender phone number
            
        Returns:
            Response from webhook
        """
        from_number = from_number or self.test_phone
        
        payload = {
            "From": f"whatsapp:{from_number}",
            "Body": text,
            "NumMedia": "0"
        }
        
        logger.info(f"Sending text message: {text}")
        
        try:
            response = requests.post(self.webhook_url, data=payload, timeout=30)
            logger.info(f"Response status: {response.status_code}")
            return {
                "status_code": response.status_code,
                "response": response.text,
                "success": response.status_code == 200
            }
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return {
                "status_code": 0,
                "error": str(e),
                "success": False
            }
    
    def send_image_message(self, image_path: str, caption: str = "", from_number: Optional[str] = None) -> Dict[str, Any]:
        """
        Simulate sending an image message.
        
        Args:
            image_path: Path to image file
            caption: Image caption
            from_number: Sender phone number
            
        Returns:
            Response from webhook
        """
        from_number = from_number or self.test_phone
        
        # In real Twilio webhook, the image would be hosted on Twilio's servers
        # For simulation, we'll use a mock URL
        mock_media_url = f"https://api.twilio.com/mock/media/{Path(image_path).name}"
        
        payload = {
            "From": f"whatsapp:{from_number}",
            "Body": caption,
            "NumMedia": "1",
            "MediaUrl0": mock_media_url,
            "MediaContentType0": "image/jpeg"
        }
        
        logger.info(f"Sending image: {image_path}")
        
        try:
            response = requests.post(self.webhook_url, data=payload, timeout=30)
            logger.info(f"Response status: {response.status_code}")
            return {
                "status_code": response.status_code,
                "response": response.text,
                "success": response.status_code == 200
            }
        except Exception as e:
            logger.error(f"Failed to send image: {e}")
            return {
                "status_code": 0,
                "error": str(e),
                "success": False
            }
    
    def simulate_patient_flow(self, patient_code: str, image_path: str) -> Dict[str, Any]:
        """
        Simulate a complete patient interaction flow.
        
        Args:
            patient_code: Patient identifier
            image_path: Path to patient's image
            
        Returns:
            Flow results
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Simulating patient flow for: {patient_code}")
        logger.info(f"{'='*60}")
        
        results = {
            "patient_code": patient_code,
            "steps": [],
            "success": False
        }
        
        # Step 1: Initial greeting
        logger.info("Step 1: Sending greeting")
        greeting_result = self.send_text_message("Hola")
        results["steps"].append({
            "step": "greeting",
            "success": greeting_result["success"],
            "response": greeting_result.get("response", "")[:200]
        })
        time.sleep(1)
        
        # Step 2: Send patient info
        logger.info("Step 2: Sending patient info")
        info_result = self.send_text_message(f"Paciente: {patient_code}")
        results["steps"].append({
            "step": "patient_info",
            "success": info_result["success"],
            "response": info_result.get("response", "")[:200]
        })
        time.sleep(1)
        
        # Step 3: Send image
        logger.info("Step 3: Sending image for analysis")
        image_result = self.send_image_message(
            image_path,
            caption=f"Imagen para análisis - Paciente {patient_code}"
        )
        results["steps"].append({
            "step": "image_analysis",
            "success": image_result["success"],
            "response": image_result.get("response", "")[:500]
        })
        
        # Determine overall success
        results["success"] = all(step["success"] for step in results["steps"])
        
        return results


def run_clinical_simulation():
    """Run clinical simulation with multiple test cases."""
    simulator = WhatsAppSimulator()
    
    # Test server connectivity first
    logger.info("Testing WhatsApp server connectivity...")
    health_url = "http://localhost:5005/health"
    try:
        health_response = requests.get(health_url, timeout=5)
        if health_response.status_code == 200:
            logger.info("✓ WhatsApp server is healthy")
        else:
            logger.warning(f"⚠ WhatsApp server health check returned: {health_response.status_code}")
    except Exception as e:
        logger.error(f"✗ WhatsApp server not reachable: {e}")
        logger.info("Make sure the WhatsApp server is running with: ./start_whatsapp_server.sh")
        return
    
    # Define test cases
    test_cases = [
        {
            "patient_code": "SIM-001",
            "image_path": "/Users/autonomos_dev/Projects/vigia/vigia_detect/cv_pipeline/tests/data/test_eritema_simple.jpg",
            "description": "Simple erythema test"
        },
        {
            "patient_code": "SIM-002",
            "image_path": "/Users/autonomos_dev/Projects/vigia/vigia_detect/cv_pipeline/tests/data/test_face_simple.jpg",
            "description": "Face image test (should be rejected)"
        }
    ]
    
    all_results = []
    
    for test_case in test_cases:
        logger.info(f"\nRunning test: {test_case['description']}")
        
        # Check if image exists
        if not Path(test_case["image_path"]).exists():
            logger.warning(f"Image not found: {test_case['image_path']}")
            continue
        
        result = simulator.simulate_patient_flow(
            test_case["patient_code"],
            test_case["image_path"]
        )
        
        result["description"] = test_case["description"]
        all_results.append(result)
        
        # Wait between tests
        time.sleep(3)
    
    # Generate summary report
    logger.info("\n" + "="*60)
    logger.info("SIMULATION SUMMARY")
    logger.info("="*60)
    
    successful = sum(1 for r in all_results if r["success"])
    total = len(all_results)
    
    logger.info(f"Total simulations: {total}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {total - successful}")
    
    for result in all_results:
        status = "✓" if result["success"] else "✗"
        logger.info(f"\n{status} {result['patient_code']} - {result.get('description', '')}")
        for step in result["steps"]:
            step_status = "✓" if step["success"] else "✗"
            logger.info(f"  {step_status} {step['step']}")
    
    # Save results
    results_file = Path(__file__).parent.parent / f"whatsapp_simulation_results_{int(time.time())}.json"
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    logger.info(f"\nResults saved to: {results_file}")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simulate WhatsApp flow for testing")
    parser.add_argument("--webhook-url", default="http://localhost:5001/webhook/whatsapp",
                        help="WhatsApp webhook URL")
    parser.add_argument("--test-message", help="Send a test text message")
    parser.add_argument("--test-image", help="Send a test image")
    
    args = parser.parse_args()
    
    simulator = WhatsAppSimulator(args.webhook_url)
    
    if args.test_message:
        result = simulator.send_text_message(args.test_message)
        print(f"Result: {json.dumps(result, indent=2)}")
    elif args.test_image:
        result = simulator.send_image_message(args.test_image)
        print(f"Result: {json.dumps(result, indent=2)}")
    else:
        run_clinical_simulation()


if __name__ == "__main__":
    main()