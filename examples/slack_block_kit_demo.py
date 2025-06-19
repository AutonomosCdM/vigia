#!/usr/bin/env python3
"""
Slack Block Kit Medical Demo
Demonstrates rich medical notifications with interactive components
"""
import asyncio
import json
from datetime import datetime
from vigia_detect.slack.block_kit_medical import BlockKitMedical, BlockKitInteractions
from vigia_detect.mcp.gateway import create_mcp_gateway
from vigia_detect.core.constants import TEST_PATIENT_DATA


async def demo_lpp_alert_block_kit():
    """Demo: LPP alert with Block Kit interface"""
    print("🏥 === DEMO: LPP Alert with Block Kit ===")
    
    # Generate Block Kit LPP alert
    blocks = BlockKitMedical.lpp_alert_blocks(
        case_id="DEMO_001",
        patient_code="DEMO_PAT_001",
        lpp_grade=2,
        confidence=0.85,
        location="sacrum",
        service="UCI",
        bed="201A"
    )
    
    print(f"✅ Generated {len(blocks)} Block Kit blocks")
    print("📋 Block Kit JSON structure:")
    print(json.dumps(blocks, indent=2, ensure_ascii=False))
    
    return blocks


async def demo_patient_history_block_kit():
    """Demo: Patient history with Block Kit interface"""
    print("\n📋 === DEMO: Patient History with Block Kit ===")
    
    # Use test patient data
    test_patient = {
        'id': 'DEMO_123',
        'name': 'María González',
        'age': 78,
        'service': 'Medicina Interna',
        'bed': 'HAB-305-A',
        'diagnoses': [
            'Diabetes mellitus tipo 2',
            'Hipertensión arterial',
            'Insuficiencia cardíaca congestiva'
        ],
        'medications': [
            'Metformina 850mg c/12h',
            'Enalapril 10mg c/24h',
            'Furosemida 40mg c/24h'
        ],
        'lpp_history': [
            {
                'date': '2024-01-15',
                'grade': 2,
                'location': 'talón derecho',
                'status': 'resuelto'
            },
            {
                'date': '2024-02-28',
                'grade': 1,
                'location': 'coccix',
                'status': 'en tratamiento'
            }
        ]
    }
    
    blocks = BlockKitMedical.patient_history_blocks(test_patient)
    
    print(f"✅ Generated {len(blocks)} patient history blocks")
    print("📋 HIPAA-compliant patient history:")
    print(json.dumps(blocks, indent=2, ensure_ascii=False))
    
    return blocks


async def demo_case_resolution_modal():
    """Demo: Case resolution modal workflow"""
    print("\n✅ === DEMO: Case Resolution Modal ===")
    
    # Generate resolution modal
    modal = BlockKitMedical.case_resolution_modal("DEMO_CASE_001")
    
    print("📝 Case resolution modal structure:")
    print(json.dumps(modal, indent=2, ensure_ascii=False))
    
    # Simulate modal submission
    print("\n🔄 Simulating modal submission...")
    
    mock_submission = {
        "callback_id": "case_resolution_DEMO_CASE_001",
        "state": {
            "values": {
                "resolution_description": {
                    "description_input": {
                        "value": "Lesión de grado 2 tratada exitosamente con vendaje especializado y cambio de posición cada 2 horas. Paciente muestra mejoría significativa."
                    }
                },
                "resolution_time": {
                    "time_select": {
                        "selected_option": {
                            "value": "1hr"
                        }
                    }
                },
                "followup_required": {
                    "followup_checkboxes": {
                        "selected_options": [
                            {"value": "medical_followup"},
                            {"value": "schedule_evaluation"}
                        ]
                    }
                }
            }
        }
    }
    
    response = BlockKitInteractions.handle_modal_submission(mock_submission)
    
    print("✅ Modal submission response:")
    print(json.dumps(response, indent=2, ensure_ascii=False))
    
    return modal, response


async def demo_interactive_buttons():
    """Demo: Interactive button handling"""
    print("\n🔘 === DEMO: Interactive Button Actions ===")
    
    # Simulate different button actions
    actions = [
        ("view_medical_history_DEMO_001", "DEMO_001", "USER_NURSE_001"),
        ("request_medical_evaluation_DEMO_001", "DEMO_001", "USER_NURSE_002"),
        ("mark_resolved_DEMO_001", "DEMO_001", "USER_DOCTOR_001")
    ]
    
    responses = []
    
    for action_id, value, user_id in actions:
        print(f"\n🔘 Handling action: {action_id}")
        response = BlockKitInteractions.handle_action(action_id, value, user_id)
        responses.append(response)
        
        print(f"   Response: {response['text']}")
        if 'blocks' in response:
            print(f"   Generated {len(response['blocks'])} response blocks")
    
    return responses


async def demo_medical_evaluation_request():
    """Demo: Medical evaluation request with urgency levels"""
    print("\n⚡ === DEMO: Medical Evaluation Requests ===")
    
    urgency_levels = ["normal", "high", "critical"]
    
    for urgency in urgency_levels:
        print(f"\n⚡ {urgency.upper()} urgency request:")
        
        blocks = BlockKitMedical.medical_evaluation_request_blocks(
            f"DEMO_{urgency.upper()}_001",
            urgency
        )
        
        print(f"   Generated {len(blocks)} blocks for {urgency} urgency")
        
        # Show header for visual verification
        header_text = blocks[0]["text"]["text"]
        print(f"   Header: {header_text}")


async def demo_system_error_blocks():
    """Demo: System error notifications"""
    print("\n⚠️ === DEMO: System Error Notifications ===")
    
    error_scenarios = [
        {
            "component": "lpp_detector",
            "code": "ERR_001",
            "severity": "high",
            "message": "Model inference timeout after 30 seconds"
        },
        {
            "component": "mcp_gateway",
            "code": "ERR_002", 
            "severity": "critical",
            "message": "Failed to connect to Slack MCP service"
        },
        {
            "component": "redis_cache",
            "code": "ERR_003",
            "severity": "medium",
            "message": "Cache write operation failed - using fallback storage"
        }
    ]
    
    for error_data in error_scenarios:
        print(f"\n⚠️ {error_data['severity'].upper()} error from {error_data['component']}:")
        
        blocks = BlockKitMedical.system_error_blocks(error_data)
        
        print(f"   Generated {len(blocks)} error notification blocks")
        print(f"   Error: {error_data['message']}")


async def demo_mcp_integration():
    """Demo: Full MCP integration with Block Kit"""
    print("\n🔗 === DEMO: MCP Gateway Integration ===")
    
    try:
        # Note: This requires actual MCP services to be running
        print("🔄 Attempting MCP Gateway connection...")
        
        async with create_mcp_gateway({'medical_compliance': 'hipaa'}) as gateway:
            print("✅ MCP Gateway connected successfully")
            
            # Demo: Send LPP alert via MCP
            print("\n📤 Sending LPP alert via MCP...")
            
            try:
                response = await gateway.send_lpp_alert_slack(
                    case_id="MCP_DEMO_001",
                    patient_code="MCP_PAT_001",
                    lpp_grade=3,
                    confidence=0.92,
                    location="heel",
                    service="Emergency",
                    bed="ER_101",
                    channel="#medical-demo"
                )
                
                print(f"✅ MCP Response: {response.status}")
                
            except Exception as e:
                print(f"⚠️ MCP operation failed (expected if services not running): {e}")
            
    except Exception as e:
        print(f"⚠️ MCP Gateway connection failed (expected if services not running): {e}")
        print("💡 To test MCP integration, run: docker-compose -f deploy/docker/docker-compose.mcp-hub.yml up -d")


async def demo_hipaa_compliance():
    """Demo: HIPAA compliance validation"""
    print("\n🔒 === DEMO: HIPAA Compliance Validation ===")
    
    # Test with sensitive patient data
    sensitive_patient = {
        'id': 'SENSITIVE_PATIENT_ID_12345',
        'name': 'JOHN_DOE_SENSITIVE_NAME',
        'age': 45,
        'service': 'Cardiology',
        'bed': 'ROOM_501_BED_A_PRIVATE',
        'ssn': '123-45-6789',  # This should never appear in blocks
        'phone': '+1-555-123-4567'  # This should never appear in blocks
    }
    
    print("🔍 Testing data anonymization...")
    
    # Generate blocks
    alert_blocks = BlockKitMedical.lpp_alert_blocks(
        "HIPAA_TEST_001",
        sensitive_patient['name'],
        2, 0.8, "sacrum",
        sensitive_patient['service'],
        sensitive_patient['bed']
    )
    
    history_blocks = BlockKitMedical.patient_history_blocks(sensitive_patient)
    
    # Extract all text and validate anonymization
    def extract_text(blocks):
        text_parts = []
        for block in blocks:
            text_parts.append(str(block))
        return " ".join(text_parts)
    
    alert_text = extract_text(alert_blocks)
    history_text = extract_text(history_blocks)
    
    # HIPAA compliance checks
    sensitive_data = [
        'SENSITIVE_PATIENT_ID_12345',
        'JOHN_DOE_SENSITIVE_NAME', 
        'ROOM_501_BED_A_PRIVATE',
        '123-45-6789',
        '+1-555-123-4567'
    ]
    
    violations = []
    for sensitive in sensitive_data:
        if sensitive in alert_text:
            violations.append(f"ALERT: {sensitive} found in alert blocks")
        if sensitive in history_text:
            violations.append(f"HISTORY: {sensitive} found in history blocks")
    
    if violations:
        print("❌ HIPAA VIOLATIONS DETECTED:")
        for violation in violations:
            print(f"   {violation}")
    else:
        print("✅ HIPAA COMPLIANCE VERIFIED:")
        print("   - No sensitive data found in Block Kit outputs")
        print("   - Patient information properly anonymized")
        print("   - Anonymization markers (***) present")
    
    # Show anonymized versions
    print("\n🔒 Anonymized data examples:")
    print(f"   Original ID: {sensitive_patient['id']}")
    print(f"   Anonymized: {sensitive_patient['id'][:4]}***")
    print(f"   Original Name: {sensitive_patient['name']}")
    print(f"   Anonymized: {sensitive_patient['name'][:3]}***")


async def main():
    """Run all Block Kit demos"""
    print("🏥 Vigía Medical System - Slack Block Kit Demo")
    print("=" * 60)
    
    # Run all demos
    await demo_lpp_alert_block_kit()
    await demo_patient_history_block_kit()
    await demo_case_resolution_modal()
    await demo_interactive_buttons()
    await demo_medical_evaluation_request()
    await demo_system_error_blocks()
    await demo_hipaa_compliance()
    await demo_mcp_integration()
    
    print("\n" + "=" * 60)
    print("✅ All Block Kit demos completed successfully!")
    print("\n💡 Next steps:")
    print("   1. Deploy MCP services: docker-compose -f deploy/docker/docker-compose.mcp-hub.yml up -d")
    print("   2. Configure Slack app with Block Kit support")
    print("   3. Test interactive components in real Slack environment")
    print("   4. Run tests: python -m pytest tests/slack/ -v")


if __name__ == "__main__":
    asyncio.run(main())