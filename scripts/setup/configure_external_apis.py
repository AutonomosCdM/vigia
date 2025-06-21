#!/usr/bin/env python3
"""
External APIs Configuration Setup
================================

Interactive setup for external service credentials and configurations.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import json
import getpass

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class ExternalAPIConfigurator:
    """Interactive configuration for external APIs"""
    
    def __init__(self):
        """Initialize configurator"""
        self.project_root = project_root
        self.env_file = self.project_root / ".env"
        self.env_template = self.project_root / ".env.development"
        self.current_config = {}
        self._load_current_config()
    
    def _load_current_config(self):
        """Load current .env configuration"""
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        self.current_config[key] = value
    
    def configure_all(self):
        """Run interactive configuration for all services"""
        print("🏥 Vigia External APIs Configuration")
        print("=" * 50)
        print("This will help you configure external service credentials.")
        print("You can skip any service by pressing Enter without entering a value.")
        print()
        
        # Configure each service
        self._configure_supabase()
        self._configure_twilio_whatsapp()
        self._configure_slack()
        self._configure_sendgrid()
        self._configure_google_cloud()
        self._configure_monitoring()
        
        # Save configuration
        self._save_configuration()
        
        print("\n✅ Configuration complete!")
        print(f"Configuration saved to: {self.env_file}")
        print("\nNext steps:")
        print("1. Start services: ./scripts/setup/setup_development_env.sh")
        print("2. Test services: python scripts/testing/test_real_services.py")
        print("3. Run application: python -m vigia_detect.api.main")
    
    def _configure_supabase(self):
        """Configure Supabase database and storage"""
        print("\n📦 Supabase Configuration")
        print("-" * 25)
        print("Get credentials from: https://supabase.com/dashboard/project/YOUR_PROJECT/settings/api")
        
        current_url = self.current_config.get('SUPABASE_URL', '')
        current_key = self.current_config.get('SUPABASE_KEY', '')
        
        if current_url:
            print(f"Current URL: {current_url[:30]}...")
        
        url = input(f"Supabase URL [{current_url[:30] + '...' if current_url else 'Skip'}]: ").strip()
        if url:
            self.current_config['SUPABASE_URL'] = url
        
        key = getpass.getpass(f"Supabase Anon Key [{'***Configured***' if current_key else 'Skip'}]: ").strip()
        if key:
            self.current_config['SUPABASE_KEY'] = key
        
        service_key = getpass.getpass("Supabase Service Role Key [Skip]: ").strip()
        if service_key:
            self.current_config['SUPABASE_SERVICE_ROLE_KEY'] = service_key
    
    def _configure_twilio_whatsapp(self):
        """Configure Twilio WhatsApp integration"""
        print("\n📱 Twilio WhatsApp Configuration")
        print("-" * 30)
        print("Get credentials from: https://console.twilio.com/")
        print("WhatsApp Sandbox: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn")
        
        current_sid = self.current_config.get('TWILIO_ACCOUNT_SID', '')
        current_token = self.current_config.get('TWILIO_AUTH_TOKEN', '')
        
        if current_sid:
            print(f"Current SID: {current_sid[:10]}...")
        
        sid = input(f"Twilio Account SID [{current_sid[:10] + '...' if current_sid else 'Skip'}]: ").strip()
        if sid:
            self.current_config['TWILIO_ACCOUNT_SID'] = sid
        
        token = getpass.getpass(f"Twilio Auth Token [{'***Configured***' if current_token else 'Skip'}]: ").strip()
        if token:
            self.current_config['TWILIO_AUTH_TOKEN'] = token
        
        from_number = input("WhatsApp From Number [whatsapp:+14155238886]: ").strip()
        if from_number:
            self.current_config['TWILIO_WHATSAPP_FROM'] = from_number
        elif 'TWILIO_WHATSAPP_FROM' not in self.current_config:
            self.current_config['TWILIO_WHATSAPP_FROM'] = 'whatsapp:+14155238886'
    
    def _configure_slack(self):
        """Configure Slack integration"""
        print("\n💬 Slack Configuration")
        print("-" * 20)
        print("Create a Slack app at: https://api.slack.com/apps")
        print("Required scopes: chat:write, files:write, users:read")
        
        current_token = self.current_config.get('SLACK_BOT_TOKEN', '')
        current_secret = self.current_config.get('SLACK_SIGNING_SECRET', '')
        
        token = getpass.getpass(f"Slack Bot Token (xoxb-...) [{'***Configured***' if current_token else 'Skip'}]: ").strip()
        if token:
            self.current_config['SLACK_BOT_TOKEN'] = token
        
        secret = getpass.getpass(f"Slack Signing Secret [{'***Configured***' if current_secret else 'Skip'}]: ").strip()
        if secret:
            self.current_config['SLACK_SIGNING_SECRET'] = secret
        
        webhook = input("Slack Webhook URL [Skip]: ").strip()
        if webhook:
            self.current_config['SLACK_WEBHOOK_URL'] = webhook
    
    def _configure_sendgrid(self):
        """Configure SendGrid email"""
        print("\n📧 SendGrid Email Configuration")
        print("-" * 30)
        print("Get API key from: https://app.sendgrid.com/settings/api_keys")
        
        current_key = self.current_config.get('SENDGRID_API_KEY', '')
        
        api_key = getpass.getpass(f"SendGrid API Key [{'***Configured***' if current_key else 'Skip'}]: ").strip()
        if api_key:
            self.current_config['SENDGRID_API_KEY'] = api_key
        
        from_email = input("From Email [noreply@yourdomain.com]: ").strip()
        if from_email:
            self.current_config['SENDGRID_FROM_EMAIL'] = from_email
        elif 'SENDGRID_FROM_EMAIL' not in self.current_config:
            self.current_config['SENDGRID_FROM_EMAIL'] = 'noreply@yourdomain.com'
    
    def _configure_google_cloud(self):
        """Configure Google Cloud / Vertex AI"""
        print("\n☁️  Google Cloud Configuration")
        print("-" * 30)
        print("For MedGemma and ADK integration")
        print("Create service account at: https://console.cloud.google.com/iam-admin/serviceaccounts")
        
        project_id = input("Google Cloud Project ID [Skip]: ").strip()
        if project_id:
            self.current_config['GOOGLE_CLOUD_PROJECT'] = project_id
        
        region = input("Vertex AI Region [us-central1]: ").strip()
        if region:
            self.current_config['VERTEX_AI_REGION'] = region
        elif 'VERTEX_AI_REGION' not in self.current_config:
            self.current_config['VERTEX_AI_REGION'] = 'us-central1'
        
        credentials_path = input("Service Account Key Path [Skip]: ").strip()
        if credentials_path:
            self.current_config['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        
        # Local AI preference
        use_local = input("Use local Ollama instead of Vertex AI? (y/N): ").lower().startswith('y')
        self.current_config['USE_LOCAL_AI'] = 'true' if use_local else 'false'
    
    def _configure_monitoring(self):
        """Configure monitoring services"""
        print("\n📊 Monitoring Configuration")
        print("-" * 25)
        
        sentry_dsn = input("Sentry DSN URL [Skip]: ").strip()
        if sentry_dsn:
            self.current_config['SENTRY_DSN'] = sentry_dsn
        
        agentops_key = getpass.getpass("AgentOps API Key [Skip]: ").strip()
        if agentops_key:
            self.current_config['AGENTOPS_API_KEY'] = agentops_key
    
    def _save_configuration(self):
        """Save configuration to .env file"""
        # Read template to preserve structure and comments
        template_content = ""
        if self.env_template.exists():
            with open(self.env_template, 'r') as f:
                template_content = f.read()
        
        # Update template with user values
        updated_content = template_content
        for key, value in self.current_config.items():
            # Replace or add the configuration
            if f"{key}=" in updated_content:
                # Replace existing value
                import re
                pattern = f"{key}=.*"
                replacement = f"{key}={value}"
                updated_content = re.sub(pattern, replacement, updated_content)
            else:
                # Add new configuration
                updated_content += f"\n{key}={value}"
        
        # Write to .env file
        with open(self.env_file, 'w') as f:
            f.write(updated_content)
    
    def show_current_config(self):
        """Show current configuration status"""
        print("\n📋 Current Configuration Status")
        print("=" * 40)
        
        services = {
            'Supabase': ['SUPABASE_URL', 'SUPABASE_KEY'],
            'Twilio WhatsApp': ['TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN'],
            'Slack': ['SLACK_BOT_TOKEN', 'SLACK_SIGNING_SECRET'],
            'SendGrid': ['SENDGRID_API_KEY'],
            'Google Cloud': ['GOOGLE_CLOUD_PROJECT'],
            'Monitoring': ['SENTRY_DSN', 'AGENTOPS_API_KEY']
        }
        
        for service_name, required_keys in services.items():
            configured_keys = [key for key in required_keys if self.current_config.get(key)]
            total_keys = len(required_keys)
            configured_count = len(configured_keys)
            
            if configured_count == total_keys:
                status = "✅ Fully Configured"
            elif configured_count > 0:
                status = f"⚠️  Partially Configured ({configured_count}/{total_keys})"
            else:
                status = "❌ Not Configured"
            
            print(f"  {service_name:<15} {status}")
        
        print(f"\nConfiguration file: {self.env_file}")


def main():
    """Main configuration function"""
    configurator = ExternalAPIConfigurator()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            configurator.show_current_config()
            return
        elif sys.argv[1] == "help":
            print("Usage: python configure_external_apis.py [command]")
            print("Commands:")
            print("  (no command)  - Interactive configuration")
            print("  status        - Show current configuration status")
            print("  help          - Show this help message")
            return
    
    configurator.configure_all()


if __name__ == "__main__":
    main()