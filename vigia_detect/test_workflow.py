"""
Test complete LPP-Detect workflow: CV Pipeline → ADK Agent → Slack Notification
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append('/Users/autonomos_dev/Projects/pressure')

from vigia_detect.agents.lpp_medical_agent import lpp_agent
from vigia_detect.cv_pipeline.detector import LPPDetector
from vigia_detect.messaging.slack_notifier import SlackNotifier

def test_cv_to_slack_workflow():
    """Test complete workflow from CV detection to Slack notification."""
    
    print("🏥 Testing LPP-Detect Complete Workflow")
    print("=" * 50)
    
    # Step 1: Mock CV Pipeline Results
    print("\n1️⃣ Simulating CV Pipeline Detection...")
    
    # Simulate different CV detection results
    test_cases = [
        {
            'case_name': 'No LPP Detected',
            'imagen_path': '/test/images/normal_skin.jpg',
            'paciente_id': 'PAT-001-TEST',
            'cv_results': {
                'detection_class': 0,
                'confidence': 0.95,
                'bbox': [100, 100, 200, 200],
                'timestamp': datetime.now().isoformat()
            }
        },
        {
            'case_name': 'LPP Grade 2 Detected',
            'imagen_path': '/test/images/grade2_ulcer.jpg', 
            'paciente_id': 'PAT-002-ULCER',
            'cv_results': {
                'detection_class': 2,
                'confidence': 0.87,
                'bbox': [150, 120, 250, 220],
                'timestamp': datetime.now().isoformat()
            }
        },
        {
            'case_name': 'LPP Grade 4 Critical',
            'imagen_path': '/test/images/grade4_critical.jpg',
            'paciente_id': 'PAT-003-CRITICAL', 
            'cv_results': {
                'detection_class': 4,
                'confidence': 0.92,
                'bbox': [80, 90, 180, 190],
                'timestamp': datetime.now().isoformat()
            }
        }
    ]
    
    # Step 2: Process each case through ADK Agent
    print("\n2️⃣ Processing through ADK Medical Agent...")
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {case['case_name']}")
        print(f"   Imagen: {case['imagen_path']}")
        print(f"   Paciente: {case['paciente_id']}")
        print(f"   CV Confidence: {case['cv_results']['confidence']:.1%}")
        
        try:
            # Simulate agent processing
            # In real implementation, this would be handled by ADK Runner
            
            # Process image through mock agent functions
            from vigia_detect.agents.lpp_medical_agent import procesar_imagen_lpp, generar_reporte_lpp
            
            # Process CV results
            result = procesar_imagen_lpp(
                imagen_path=case['imagen_path'],
                paciente_id=case['paciente_id'],
                resultados_cv=case['cv_results']
            )
            
            print(f"   ✅ Agent Processing: {result['status']}")
            print(f"   📊 Severidad: Grado {result['severidad']}")
            print(f"   📋 Require Notification: {result['require_notification']}")
            
            # Generate medical report
            reporte = generar_reporte_lpp(
                paciente_id=result['paciente_id'],
                severidad=result['severidad'], 
                confianza=case['cv_results']['confidence']
            )
            
            print(f"   📄 Reporte: {reporte['clasificacion']}")
            print(f"   🚨 Urgencia: {reporte['nivel_urgencia']}")
            
            # Step 3: Send Slack notification if required
            if result['require_notification']:
                print(f"   📤 Sending Slack notification...")
                
                # Use Slack integration
                from vigia_detect.messaging.adk_tools import enviar_alerta_lpp
                
                slack_result = enviar_alerta_lpp(
                    canal="#project-lpp",  # Use existing channel
                    severidad=result['severidad'],
                    paciente_id=result['paciente_id'],
                    detalles=result['detalles']
                )
                
                if slack_result['status'] == 'success':
                    print(f"   ✅ Slack notification sent successfully")
                else:
                    print(f"   ❌ Slack notification failed: {slack_result['error']}")
            else:
                print(f"   ℹ️ No notification required (Grade 0)")
                
        except Exception as e:
            print(f"   ❌ Error processing case: {e}")
    
    print("\n🎉 Workflow Testing Completed!")
    print("\nWorkflow Summary:")
    print("1. CV Pipeline → Detect LPP in images")
    print("2. ADK Agent → Process results + Generate medical report")  
    print("3. Slack Notification → Alert medical team based on severity")
    print("\nNext Steps:")
    print("- Integrate with real YOLOv5 model")
    print("- Add ADK Runner for proper session management")
    print("- Connect with WhatsApp for patient communication")

def test_adk_agent_direct():
    """Test ADK agent directly with mock conversation."""
    
    print("\n🤖 Testing ADK Agent Direct Interaction")
    print("=" * 40)
    
    try:
        # Test agent response to medical query
        print("Sending test query to LPP agent...")
        
        # This would normally be done through ADK Runner
        # For now, we'll test the agent setup
        
        print(f"✅ Agent configured: {lpp_agent.name}")
        print(f"📋 Model: {lpp_agent.model}")
        print(f"🔧 Tools available: {len(lpp_agent.tools)}")
        
        tool_names = []
        for tool in lpp_agent.tools:
            if hasattr(tool, '__name__'):
                tool_names.append(tool.__name__)
            else:
                tool_names.append(str(tool))
        
        print(f"🛠️ Tools: {', '.join(tool_names)}")
        
        print("✅ ADK Agent ready for integration!")
        
    except Exception as e:
        print(f"❌ Agent setup error: {e}")

if __name__ == "__main__":
    # Test complete workflow
    test_cv_to_slack_workflow()
    
    # Test ADK agent setup
    test_adk_agent_direct()
