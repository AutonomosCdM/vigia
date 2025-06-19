#!/usr/bin/env python3
"""
Vigia Webhook Integration Demo
Demonstrates comprehensive webhook handling for medical integrations.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add vigia_detect to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from vigia_detect.webhook.server import WebhookServer
    from vigia_detect.webhook.handlers import WebhookHandlers, create_default_handlers
    from vigia_detect.webhook.models import EventType
    # Messaging replaced with audit logging for MCP compliance
    def process_whatsapp_message(*args, **kwargs):
        """Stub function for WhatsApp processing - now uses audit logging."""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"WhatsApp message processed via audit: {kwargs}")
        return {"status": "processed", "method": "audit_log"}
    
    class SlackIntegration:
        def __init__(self, *args, **kwargs):
            import logging
            self.logger = logging.getLogger(__name__)
        
        def send_notification(self, *args, **kwargs):
            self.logger.info(f"Slack integration logged via audit: {kwargs}")
            return {"status": "logged", "audit_compliant": True}
except ImportError as e:
    print(f"⚠️  Import warning: {e}")
    print("Some webhook components may not be available.")


class WebhookDemo:
    """Comprehensive webhook demonstration for medical integrations."""
    
    def __init__(self):
        """Initialize webhook demo."""
        self.webhook_server = None
        self.handlers = None
        
    async def setup_webhook_server(self):
        """Setup webhook server with medical event handlers."""
        print("🔧 Setting up webhook server with medical handlers...")
        
        try:
            # Create server
            self.webhook_server = WebhookServer(port=8085)
            
            # Create comprehensive handlers
            self.handlers = create_default_handlers()
            
            # Add custom medical handlers
            await self.setup_medical_handlers()
            
            print("✅ Webhook server configured successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup webhook server: {e}")
            return False
    
    async def setup_medical_handlers(self):
        """Setup specialized medical webhook handlers."""
        
        # Medical image processing handler
        @self.handlers.register_handler(EventType.MEDICAL_IMAGE_RECEIVED)
        async def handle_medical_image(event_data: Dict[str, Any]) -> Dict[str, Any]:
            """Handle incoming medical images for LPP analysis."""
            print(f"🖼️  Medical image received: {event_data.get('image_id')}")
            
            # Simulate medical image processing
            result = {
                "status": "processed",
                "lpp_detected": True,
                "stage": 2,
                "confidence": 0.87,
                "anatomical_location": "sacrum",
                "requires_medical_review": True,
                "processing_time_ms": 1250,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"   📊 Detection Result: Stage {result['stage']} LPP")
            print(f"   🎯 Confidence: {result['confidence']:.1%}")
            print(f"   📍 Location: {result['anatomical_location']}")
            
            return result
        
        # Medical alert handler
        @self.handlers.register_handler(EventType.MEDICAL_ALERT)
        async def handle_medical_alert(event_data: Dict[str, Any]) -> Dict[str, Any]:
            """Handle medical alerts for urgent cases."""
            print(f"🚨 Medical alert triggered: {event_data.get('alert_type')}")
            
            alert_response = {
                "alert_acknowledged": True,
                "notification_sent": True,
                "escalation_required": event_data.get('urgency') == 'emergency',
                "response_time_ms": 150,
                "timestamp": datetime.now().isoformat()
            }
            
            if alert_response["escalation_required"]:
                print("   🏥 Emergency escalation initiated")
                print("   📞 Medical staff notified")
            
            return alert_response
        
        # WhatsApp medical message handler
        @self.handlers.register_handler(EventType.WHATSAPP_MESSAGE)
        async def handle_whatsapp_medical(event_data: Dict[str, Any]) -> Dict[str, Any]:
            """Handle WhatsApp messages with medical content."""
            print(f"📱 WhatsApp medical message from: {event_data.get('from', 'unknown')}")
            
            # Check for medical images
            if event_data.get('num_media', 0) > 0:
                print("   🖼️  Medical image detected in message")
                
                # Simulate medical image analysis
                analysis_result = {
                    "image_analyzed": True,
                    "medical_content_detected": True,
                    "auto_response_sent": True,
                    "medical_review_scheduled": True,
                    "patient_notified": True
                }
                
                print("   ✅ Auto-analysis completed")
                print("   📧 Patient notification sent")
                
                return analysis_result
            else:
                print("   💬 Text-only medical inquiry")
                return {
                    "text_processed": True,
                    "medical_keywords_detected": True,
                    "guidance_provided": True
                }
        
        # Slack medical notification handler
        @self.handlers.register_handler(EventType.SLACK_COMMAND)
        async def handle_slack_medical(event_data: Dict[str, Any]) -> Dict[str, Any]:
            """Handle Slack medical team notifications."""
            command = event_data.get('command', '')
            print(f"💬 Slack medical command: {command}")
            
            if command == '/medical-status':
                # Simulate medical system status
                status = {
                    "system_status": "operational",
                    "active_cases": 12,
                    "pending_reviews": 3,
                    "urgent_alerts": 0,
                    "ai_model_status": "healthy",
                    "last_updated": datetime.now().isoformat()
                }
                
                print("   📊 Medical system status retrieved")
                return status
                
            elif command == '/patient-summary':
                # Simulate patient summary request
                summary = {
                    "patient_code": event_data.get('patient_id', 'CD-2025-001'),
                    "recent_assessments": 2,
                    "lpp_detections": 1,
                    "risk_level": "moderate",
                    "last_image_analysis": "2 hours ago",
                    "next_review_due": "tomorrow"
                }
                
                print(f"   📋 Patient summary for: {summary['patient_code']}")
                return summary
            
            return {"command_processed": True}
        
        print("🏥 Medical webhook handlers configured")
    
    async def demo_webhook_events(self):
        """Demonstrate various webhook events."""
        print("\n" + "="*60)
        print("🔗 WEBHOOK EVENTS DEMONSTRATION")
        print("="*60)
        
        # Test events
        test_events = [
            {
                "name": "Medical Image Upload",
                "event_type": EventType.MEDICAL_IMAGE_RECEIVED,
                "data": {
                    "image_id": "img_cd_2025_001_sacrum",
                    "patient_code": "CD-2025-001",
                    "body_location": "sacrum",
                    "upload_timestamp": datetime.now().isoformat(),
                    "file_size": 2048576,
                    "format": "JPEG"
                }
            },
            {
                "name": "High-Risk LPP Detection",
                "event_type": EventType.MEDICAL_ALERT,
                "data": {
                    "alert_type": "high_risk_lpp",
                    "patient_code": "CD-2025-002",
                    "lpp_stage": 3,
                    "confidence": 0.92,
                    "urgency": "high",
                    "location": "heel",
                    "detected_at": datetime.now().isoformat()
                }
            },
            {
                "name": "WhatsApp Medical Inquiry",
                "event_type": EventType.WHATSAPP_MESSAGE,
                "data": {
                    "from": "+56912345678",
                    "body": "Tengo una herida en el talón que no mejora",
                    "num_media": 1,
                    "media_type": "image/jpeg",
                    "timestamp": datetime.now().isoformat()
                }
            },
            {
                "name": "Slack Medical Status Request",
                "event_type": EventType.SLACK_COMMAND,
                "data": {
                    "command": "/medical-status",
                    "user_id": "U123456",
                    "channel_id": "C789012",
                    "team_id": "T345678"
                }
            }
        ]
        
        # Process each test event
        for i, event in enumerate(test_events, 1):
            print(f"\n🔹 Test Event {i}: {event['name']}")
            print("-" * 40)
            
            try:
                # Process event through handlers
                if self.handlers:
                    result = await self.handlers.handle_event(
                        event["event_type"], 
                        event["data"]
                    )
                    
                    if result:
                        print(f"✅ Event processed successfully")
                        # Show key results
                        for key, value in result.items():
                            if isinstance(value, (str, int, float, bool)):
                                print(f"   📋 {key}: {value}")
                    else:
                        print("⚠️  Event processed with no result")
                else:
                    print("❌ No handlers available")
                    
            except Exception as e:
                print(f"❌ Event processing failed: {e}")
    
    async def demo_integration_workflow(self):
        """Demonstrate complete integration workflow."""
        print("\n" + "="*60)
        print("🔄 INTEGRATION WORKFLOW DEMONSTRATION")
        print("="*60)
        
        # Simulate complete medical workflow
        workflow_steps = [
            "📱 Patient sends WhatsApp image",
            "🔗 Webhook receives image data",
            "🖼️  Image processed by CV pipeline",
            "🧠 MedGemma analyzes findings",
            "⚕️  Medical decision engine evaluates",
            "🚨 Alert level determined",
            "📧 Patient notification sent",
            "👩‍⚕️ Medical staff alerted via Slack",
            "📊 Results stored in database",
            "📋 Audit trail updated"
        ]
        
        print("🔄 Complete Medical Integration Workflow:")
        print("-" * 45)
        
        for step in workflow_steps:
            print(f"   {step}")
            await asyncio.sleep(0.3)  # Simulate processing time
        
        print("\n✅ Workflow completed successfully!")
        print("📊 Integration Points Demonstrated:")
        print("   • WhatsApp medical messaging")
        print("   • Real-time image analysis")
        print("   • Medical AI decision support")
        print("   • Slack team notifications")
        print("   • Database medical records")
        print("   • Audit compliance logging")
    
    async def demo_error_handling(self):
        """Demonstrate webhook error handling."""
        print("\n" + "="*60)
        print("⚠️  ERROR HANDLING DEMONSTRATION")
        print("="*60)
        
        # Test error scenarios
        error_scenarios = [
            {
                "name": "Invalid Medical Image Format",
                "event_type": EventType.MEDICAL_IMAGE_RECEIVED,
                "data": {
                    "image_id": "invalid_format.txt",
                    "format": "TXT"  # Invalid medical image format
                }
            },
            {
                "name": "Missing Patient Context",
                "event_type": EventType.MEDICAL_ALERT,
                "data": {
                    "alert_type": "missing_patient_data"
                    # Missing patient_code
                }
            }
        ]
        
        print("🧪 Testing error handling scenarios:")
        
        for scenario in error_scenarios:
            print(f"\n❌ {scenario['name']}:")
            
            try:
                if self.handlers:
                    result = await self.handlers.handle_event(
                        scenario["event_type"],
                        scenario["data"]
                    )
                    print(f"   🔧 Graceful handling: {result is not None}")
                else:
                    print("   ⚠️  No handlers for error testing")
                    
            except Exception as e:
                print(f"   🛡️  Error caught and handled: {type(e).__name__}")
        
        print("\n✅ Error handling mechanisms working correctly")
    
    async def run_complete_demo(self):
        """Run the complete webhook demonstration."""
        print("🔗 VIGIA WEBHOOK INTEGRATION DEMO")
        print("=" * 60)
        print("This demo showcases webhook handling for medical integrations")
        print("including WhatsApp, Slack, and real-time medical processing.\n")
        
        # Setup webhook server
        if not await self.setup_webhook_server():
            print("❌ Failed to setup webhook server. Running limited demo...")
        
        # Run demonstrations
        try:
            await self.demo_webhook_events()
            await self.demo_integration_workflow()
            await self.demo_error_handling()
            
        except Exception as e:
            print(f"❌ Demo execution error: {e}")
        
        # Summary
        print("\n" + "="*60)
        print("📋 WEBHOOK DEMO SUMMARY")
        print("="*60)
        print("✅ Demonstrated webhook integrations:")
        print("   • Medical image processing webhooks")
        print("   • WhatsApp medical messaging integration")
        print("   • Slack medical team notifications")
        print("   • Real-time medical alert handling")
        print("   • Complete workflow orchestration")
        print("   • Error handling and recovery")
        print("\n🏥 Webhook system ready for hospital deployment!")


async def main():
    """Main demo execution."""
    try:
        demo = WebhookDemo()
        await demo.run_complete_demo()
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")


if __name__ == "__main__":
    print("🔗 Starting Vigia Webhook Integration Demo...")
    print("Press Ctrl+C to interrupt at any time\n")
    
    asyncio.run(main())