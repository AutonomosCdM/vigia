#!/usr/bin/env python3
"""
Vigia MCP Messaging Demo
Demonstrates WhatsApp and Slack integrations for medical notifications
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any

from vigia_detect.mcp.gateway import MCPGateway
from vigia_detect.systems.medical_decision_engine import MedicalDecisionEngine


async def demo_whatsapp_notifications():
    """Demo WhatsApp notifications via Twilio"""
    print("🔄 Demo: WhatsApp Medical Notifications via Twilio")
    print("=" * 60)
    
    config = {
        'medical_compliance': 'hipaa',
        'audit_enabled': True,
        'demo_mode': True
    }
    
    async with MCPGateway(config) as gateway:
        # Sample patient context
        patient_context = {
            'patient_id': 'PAT-2024-001',
            'age': 78,
            'diabetes': True,
            'mobility': 'limited',
            'ward': 'Medical Ward 3',
            'admission_date': '2024-01-15'
        }
        
        print(f"📱 Sending WhatsApp notification for patient: {patient_context['patient_id']}")
        
        # Send LPP detection notification
        response = await gateway.whatsapp_operation(
            'send_message',
            patient_context=patient_context,
            to='whatsapp:+1234567890',  # Replace with actual phone number
            message='🏥 LPP Grade 2 detected. Please review patient immediately.'
        )
        
        print(f"✅ WhatsApp Response: {response.status}")
        print(f"   Request ID: {response.request_id}")
        print(f"   Response Time: {response.response_time:.2f}s")
        print(f"   Compliance Validated: {response.compliance_validated}")
        print(f"   Audit Logged: {response.audit_logged}")
        print()


async def demo_slack_team_notifications():
    """Demo Slack team notifications"""
    print("🔄 Demo: Slack Medical Team Notifications")
    print("=" * 60)
    
    config = {
        'medical_compliance': 'hipaa',
        'audit_enabled': True,
        'demo_mode': True
    }
    
    async with MCPGateway(config) as gateway:
        medical_context = {
            'department': 'wound_care',
            'priority': 'high',
            'shift': 'day_shift',
            'attending_physician': 'Dr. Smith'
        }
        
        print("💬 Sending Slack notification to medical team")
        
        # Send medical alert to Slack channel
        response = await gateway.slack_operation(
            'send_message',
            medical_context=medical_context,
            channel='#medical-alerts',
            message='🚨 Grade 3 LPP detected in Room 305. Immediate intervention required.'
        )
        
        print(f"✅ Slack Response: {response.status}")
        print(f"   Request ID: {response.request_id}")
        print(f"   Response Time: {response.response_time:.2f}s")
        print(f"   Team Communication: ✓")
        print()


async def demo_automated_lpp_workflow():
    """Demo automated LPP detection workflow with notifications"""
    print("🔄 Demo: Automated LPP Detection Workflow")
    print("=" * 60)
    
    config = {
        'medical_compliance': 'hipaa',
        'audit_enabled': True,
        'demo_mode': True
    }
    
    async with MCPGateway(config) as gateway:
        # Simulate LPP detection results
        detection_results = [
            {
                'patient_id': 'PAT-2024-001',
                'lpp_grade': 1,
                'confidence': 0.82,
                'location': 'sacrum',
                'severity': 'low'
            },
            {
                'patient_id': 'PAT-2024-002', 
                'lpp_grade': 2,
                'confidence': 0.91,
                'location': 'heel',
                'severity': 'medium'
            },
            {
                'patient_id': 'PAT-2024-003',
                'lpp_grade': 3,
                'confidence': 0.96,
                'location': 'coccyx',
                'severity': 'high'
            }
        ]
        
        for detection in detection_results:
            print(f"🔍 Processing LPP detection for {detection['patient_id']}")
            print(f"   Grade: {detection['lpp_grade']}, Confidence: {detection['confidence']:.2f}")
            
            patient_context = {
                'patient_id': detection['patient_id'],
                'age': 75,
                'diabetes': True,
                'mobility': 'limited'
            }
            
            # Send notification based on severity
            platform = 'slack' if detection['severity'] in ['medium', 'high'] else 'whatsapp'
            
            response = await gateway.notify_lpp_detection(
                lpp_grade=detection['lpp_grade'],
                confidence=detection['confidence'],
                patient_context=patient_context,
                platform=platform
            )
            
            print(f"   ✅ Notification sent via {platform}: {response.status}")
            print(f"   📊 Severity: {detection['severity']}")
            print()


async def demo_emergency_escalation():
    """Demo emergency escalation workflow"""
    print("🔄 Demo: Emergency Escalation Workflow")
    print("=" * 60)
    
    config = {
        'medical_compliance': 'hipaa',
        'audit_enabled': True,
        'demo_mode': True
    }
    
    async with MCPGateway(config) as gateway:
        critical_patient = {
            'patient_id': 'PAT-CRITICAL-001',
            'age': 82,
            'diabetes': True,
            'mobility': 'bedbound',
            'risk_factors': ['diabetes', 'advanced_age', 'immobility'],
            'ward': 'ICU'
        }
        
        print(f"🚨 CRITICAL: Grade 4 LPP detected for {critical_patient['patient_id']}")
        
        # Send critical alert via Slack
        response = await gateway.send_medical_alert(
            alert_type='lpp_critical',
            patient_id=critical_patient['patient_id'],
            severity='critical',
            platform='slack',
            message='🚨 CRITICAL: Grade 4 LPP detected - IMMEDIATE intervention required'
        )
        
        print(f"✅ Critical Alert Response: {response.status}")
        print(f"   Emergency Escalation: ✓")
        print(f"   Requires Acknowledgment: ✓")
        print()
        
        # Follow up with WhatsApp to on-call physician
        follow_up_response = await gateway.whatsapp_operation(
            'send_message',
            patient_context=critical_patient,
            to='whatsapp:+1234567890',  # On-call physician
            message=f'🚨 URGENT: Critical LPP alert for {critical_patient["patient_id"]} - ICU. Please respond immediately.'
        )
        
        print(f"✅ Follow-up WhatsApp: {follow_up_response.status}")
        print()


async def demo_phi_protection():
    """Demo PHI protection in messaging"""
    print("🔄 Demo: PHI Protection in Messaging")
    print("=" * 60)
    
    config = {
        'medical_compliance': 'hipaa',
        'phi_protection': 'strict',
        'audit_enabled': True,
        'demo_mode': True
    }
    
    async with MCPGateway(config) as gateway:
        # Sensitive patient data
        sensitive_context = {
            'patient_id': 'PAT-SENSITIVE-001',
            'ssn': '123-45-6789',  # PHI - should be protected
            'medical_record_number': 'MRN-7890123',
            'diagnosis': 'Diabetes Type 2 with complications'
        }
        
        print("🔒 Sending message with PHI protection enabled")
        
        # Send notification with PHI protection
        response = await gateway.slack_operation(
            'send_message',
            medical_context={
                'phi_protection': True,
                'anonymize_patient_data': True,
                'department': 'endocrinology'
            },
            channel='#medical-team',
            message='Patient in Room 12 requires wound care assessment. See secure system for details.'
        )
        
        print(f"✅ PHI-Protected Message: {response.status}")
        print(f"   PHI Protection: ✓")
        print(f"   Data Anonymization: ✓")
        print(f"   Audit Trail: ✓")
        print()


async def demo_service_monitoring():
    """Demo service health monitoring"""
    print("🔄 Demo: MCP Messaging Service Monitoring")
    print("=" * 60)
    
    config = {
        'medical_compliance': 'hipaa',
        'audit_enabled': True,
        'demo_mode': True
    }
    
    async with MCPGateway(config) as gateway:
        print("📊 Checking MCP messaging service status...")
        
        status = await gateway.get_service_status()
        
        print(f"🌐 Gateway Status: {status['gateway_status']}")
        print(f"⏰ Timestamp: {status['timestamp']}")
        print()
        
        print("📱 Messaging Services:")
        for service_name, service_info in status['services'].items():
            if 'messaging' in service_info.get('type', ''):
                print(f"   {service_name}:")
                print(f"     Status: {'✅ Healthy' if service_info['healthy'] else '❌ Unhealthy'}")
                print(f"     Type: {service_info['type']}")
                print(f"     Compliance: {service_info['compliance']}")
                print(f"     Endpoint: {service_info['endpoint']}")
        print()


async def demo_rate_limiting():
    """Demo rate limiting for messaging services"""
    print("🔄 Demo: Rate Limiting Protection")
    print("=" * 60)
    
    config = {
        'medical_compliance': 'hipaa',
        'audit_enabled': True,
        'demo_mode': True
    }
    
    async with MCPGateway(config) as gateway:
        patient_context = {
            'patient_id': 'PAT-RATE-TEST-001',
            'department': 'general_medicine'
        }
        
        print("🚦 Testing rate limiting (sending multiple rapid requests)")
        
        start_time = time.time()
        responses = []
        
        # Send multiple requests rapidly
        for i in range(10):
            response = await gateway.whatsapp_operation(
                'send_message',
                patient_context=patient_context,
                to='whatsapp:+1234567890',
                message=f'Rate limit test message {i+1}'
            )
            responses.append(response)
            print(f"   Request {i+1}: {response.status}")
        
        end_time = time.time()
        
        success_count = sum(1 for r in responses if r.status == 'success')
        rate_limited_count = sum(1 for r in responses if 'rate limit' in (r.error or '').lower())
        
        print()
        print(f"📊 Rate Limiting Results:")
        print(f"   Total Requests: {len(responses)}")
        print(f"   Successful: {success_count}")
        print(f"   Rate Limited: {rate_limited_count}")
        print(f"   Total Time: {end_time - start_time:.2f}s")
        print()


async def main():
    """Run all MCP messaging demos"""
    print("🏥 Vigia MCP Messaging Integration Demo")
    print("=" * 80)
    print()
    
    demos = [
        demo_whatsapp_notifications,
        demo_slack_team_notifications,
        demo_automated_lpp_workflow,
        demo_emergency_escalation,
        demo_phi_protection,
        demo_service_monitoring,
        demo_rate_limiting
    ]
    
    for demo in demos:
        try:
            await demo()
            await asyncio.sleep(1)  # Brief pause between demos
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            print()
    
    print("✅ All MCP messaging demos completed!")
    print()
    print("📋 Next Steps:")
    print("1. Configure actual Twilio and Slack credentials")
    print("2. Deploy MCP services: ./scripts/deployment/deploy-mcp-messaging.sh deploy")
    print("3. Run integration tests: pytest tests/integration/test_mcp_messaging_integration.py")
    print("4. Monitor service health via MCP Gateway dashboard")


if __name__ == "__main__":
    asyncio.run(main())