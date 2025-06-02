"""
Test script for Slack integration with LPP-Detect system.
Validates Slack Bot connectivity and notification functionality.
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append('/Users/autonomos_dev/Projects/pressure')

from vigia_detect.messaging.slack_notifier import SlackNotifier

def test_slack_basic():
    """Test basic Slack connectivity."""
    print("🔧 Testing Slack connectivity...")
    
    notifier = SlackNotifier()
    
    # Test getting channels
    result = notifier.obtener_canales()
    if result['status'] == 'success':
        print(f"✅ Connected to Slack workspace")
        print(f"📋 Available channels: {len(result['canales'])}")
        for canal in result['canales'][:3]:  # Show first 3
            print(f"   - #{canal['name']} ({canal['id']})")
    else:
        print(f"❌ Failed to connect: {result['error']}")
        return False
    
    return True

def test_notification_system():
    """Test LPP notification system with sample data."""
    print("\n🧪 Testing LPP notification system...")
    
    notifier = SlackNotifier()
    
    # Test data for different severity levels
    test_cases = [
        {
            'severidad': 0,
            'paciente_id': 'PAT-001-TEST',
            'detalles': {
                'confidence': 95.2,
                'timestamp': datetime.now().isoformat(),
                'ubicacion': 'Sacro',
                'imagen_path': '/test/image.jpg'
            }
        },
        {
            'severidad': 2,
            'paciente_id': 'PAT-002-TEST', 
            'detalles': {
                'confidence': 87.4,
                'timestamp': datetime.now().isoformat(),
                'ubicacion': 'Talón derecho',
                'imagen_path': '/test/image2.jpg'
            }
        },
        {
            'severidad': 4,
            'paciente_id': 'PAT-003-CRITICAL',
            'detalles': {
                'confidence': 92.1,
                'timestamp': datetime.now().isoformat(),
                'ubicacion': 'Región glútea',
                'imagen_path': '/test/critical.jpg'
            }
        }
    ]
    
    # Use a test channel (you may need to create #lpp-test)
    test_channel = "#general"  # Change to #lpp-test when available
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📤 Test {i}: Sending severity {case['severidad']} notification...")
        
        result = notifier.notificar_deteccion_lpp(
            canal=test_channel,
            severidad=case['severidad'],
            paciente_id=case['paciente_id'],
            detalles=case['detalles']
        )
        
        if result['status'] == 'success':
            print(f"✅ Notification sent successfully")
        else:
            print(f"❌ Failed to send: {result['error']}")
    
    return True

def main():
    """Main test execution."""
    print("🏥 LPP-Detect Slack Integration Test")
    print("=" * 40)
    
    # Basic connectivity test
    if not test_slack_basic():
        print("\n❌ Basic connectivity failed. Check token and permissions.")
        return
    
    # Notification system test
    test_notification_system()
    
    print("\n🎉 Testing completed!")
    print("\nNext steps:")
    print("1. Create #lpp-alerts channel in Slack")
    print("2. Integrate with ADK agents") 
    print("3. Test with real CV pipeline results")

if __name__ == "__main__":
    main()
