#!/usr/bin/env python3
"""
Demo script showing how to use webhook handlers with the WebhookServer.

This example demonstrates:
1. Setting up a webhook server with custom handlers
2. Processing different event types
3. Integration with other services (Slack, WhatsApp, DB, Redis)
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add vigia_detect to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from vigia_detect.webhook.server import WebhookServer
from vigia_detect.webhook.handlers import WebhookHandlers, create_default_handlers
from vigia_detect.webhook.models import EventType


async def setup_webhook_server_with_handlers():
    """Setup webhook server with comprehensive event handlers."""
    
    # Create server
    server = WebhookServer(port=8085)
    
    # Create handlers with desired integrations
    # In production, these would be configured via environment variables
    handlers = create_default_handlers({
        'enable_slack': False,  # Set to True if Slack is configured
        'enable_twilio': False,  # Set to True if Twilio is configured
        'enable_db': False,  # Set to True if Supabase is configured
        'enable_redis': False  # Set to True if Redis is configured
    })
    
    # Register handlers for each event type
    
    @server.on_event(EventType.DETECTION_COMPLETED)
    async def on_detection_completed(event_type, payload):
        """Handle detection completed events."""
        print(f"\n📸 Processing DETECTION_COMPLETED event")
        result = await handlers.handle_detection_completed(event_type, payload)
        
        # Custom processing
        risk_level = payload.get('risk_level')
        if risk_level == 'CRITICAL':
            print("  🚨 CRITICAL case - triggering emergency protocol")
            # Trigger emergency protocol
            await trigger_emergency_protocol(payload)
        
        return result
    
    @server.on_event(EventType.DETECTION_FAILED)
    async def on_detection_failed(event_type, payload):
        """Handle detection failure events."""
        print(f"\n❌ Processing DETECTION_FAILED event")
        result = await handlers.handle_detection_failed(event_type, payload)
        
        # Custom error tracking
        error_count = await increment_error_counter(payload.get('patient_code'))
        if error_count > 3:
            print("  ⚠️ Multiple failures detected - alerting technical team")
        
        return result
    
    @server.on_event(EventType.PATIENT_UPDATED)
    async def on_patient_updated(event_type, payload):
        """Handle patient update events."""
        print(f"\n👤 Processing PATIENT_UPDATED event")
        result = await handlers.handle_patient_updated(event_type, payload)
        
        # Custom business logic
        update_type = payload.get('update_type')
        if update_type == 'discharge':
            print("  📋 Patient discharged - archiving records")
            await archive_patient_data(payload.get('patient_code'))
        
        return result
    
    @server.on_event(EventType.PROTOCOL_TRIGGERED)
    async def on_protocol_triggered(event_type, payload):
        """Handle protocol trigger events."""
        print(f"\n⚡ Processing PROTOCOL_TRIGGERED event")
        result = await handlers.handle_protocol_triggered(event_type, payload)
        
        # Custom protocol handling
        protocol_name = payload.get('protocol_name')
        print(f"  📋 Executing protocol: {protocol_name}")
        print(f"  📍 Actions: {len(payload.get('actions', []))}")
        
        return result
    
    @server.on_event(EventType.ANALYSIS_READY)
    async def on_analysis_ready(event_type, payload):
        """Handle analysis ready events."""
        print(f"\n📊 Processing ANALYSIS_READY event")
        result = await handlers.handle_analysis_ready(event_type, payload)
        
        # Custom analysis processing
        analysis_type = payload.get('analysis_type')
        if analysis_type == 'trend_analysis':
            print("  📈 Trend analysis complete - updating dashboards")
            await update_dashboards(payload)
        
        return result
    
    return server


# Custom helper functions (these would be implemented based on your needs)

async def trigger_emergency_protocol(payload):
    """Trigger emergency protocol for critical cases."""
    patient_code = payload.get('patient_code')
    print(f"    → Paging on-call physician for {patient_code}")
    print(f"    → Preparing emergency care resources")
    print(f"    → Updating patient status to CRITICAL")
    await asyncio.sleep(0.1)  # Simulate async operation


async def increment_error_counter(patient_code):
    """Track detection errors per patient."""
    # In production, this would use Redis or a database
    print(f"    → Incrementing error counter for {patient_code}")
    return 4  # Mock return value


async def archive_patient_data(patient_code):
    """Archive patient data on discharge."""
    print(f"    → Archiving data for {patient_code}")
    print(f"    → Moving to cold storage")
    await asyncio.sleep(0.1)  # Simulate async operation


async def update_dashboards(payload):
    """Update monitoring dashboards with new analysis."""
    print(f"    → Updating dashboard widgets")
    print(f"    → Refreshing trend graphs")
    await asyncio.sleep(0.1)  # Simulate async operation


def demonstrate_webhook_handlers():
    """Demonstrate the webhook handler system."""
    print("🎯 Webhook Handler System Demo")
    print("=" * 60)
    print("\nThis demo shows how webhook handlers process different events:")
    print("  • DETECTION_COMPLETED - Process detection results")
    print("  • DETECTION_FAILED - Handle processing errors")
    print("  • PATIENT_UPDATED - Track patient changes")
    print("  • PROTOCOL_TRIGGERED - Execute medical protocols")
    print("  • ANALYSIS_READY - Handle completed analyses")
    
    print("\n📋 Handler Features:")
    print("  • Automatic risk assessment and notifications")
    print("  • Integration with Slack, WhatsApp, Database, Redis")
    print("  • Custom business logic per event type")
    print("  • Error tracking and recovery")
    print("  • Protocol task creation and tracking")
    
    print("\n💡 Usage in Production:")
    print("  1. Configure integrations via environment variables")
    print("  2. Register handlers with your webhook server")
    print("  3. Customize handler logic for your workflows")
    print("  4. Monitor handler performance and errors")
    
    print("\n🔧 Example Configuration:")
    print("""
    # Environment variables
    export SLACK_WEBHOOK_URL="https://hooks.slack.com/..."
    export TWILIO_ACCOUNT_SID="AC..."
    export SUPABASE_URL="https://....supabase.co"
    export REDIS_URL="redis://localhost:6379"
    
    # Create handlers with integrations
    handlers = create_default_handlers({
        'enable_slack': True,
        'enable_twilio': True,
        'enable_db': True,
        'enable_redis': True
    })
    """)


async def run_demo():
    """Run the webhook handler demo."""
    # Setup server with handlers
    server = await setup_webhook_server_with_handlers()
    
    print("\n🚀 Webhook server configured with handlers")
    print(f"   Registered event types: {len(server.event_handlers)}")
    
    for event_type, handlers in server.event_handlers.items():
        print(f"   • {event_type.value}: {len(handlers)} handler(s)")
    
    print("\n✅ Server ready to process webhook events!")
    print("\n💡 In production, start the server with:")
    print("   server.run(host='0.0.0.0', port=8080)")


if __name__ == "__main__":
    # Show demo information
    demonstrate_webhook_handlers()
    
    # Run async demo
    print("\n" + "=" * 60)
    print("Running handler setup demo...")
    asyncio.run(run_demo())