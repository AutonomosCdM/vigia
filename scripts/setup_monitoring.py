#!/usr/bin/env python3
"""
Vigia v1.0.0-rc1 Monitoring Setup
Sets up structured logging and monitoring capabilities
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

# Create monitoring directories
def create_monitoring_structure():
    """Create necessary monitoring directories and files"""
    base_dir = Path(__file__).parent.parent
    
    # Create directories
    dirs = [
        base_dir / "monitoring",
        base_dir / "monitoring" / "grafana" / "dashboards",
        base_dir / "logs",
    ]
    
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {dir_path}")

def create_prometheus_config():
    """Create Prometheus configuration"""
    prometheus_config = """
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'vigia-app'
    static_configs:
      - targets: ['vigia:8080']
        labels:
          service: 'detection'
          
  - job_name: 'vigia-whatsapp'
    static_configs:
      - targets: ['whatsapp:5000']
        labels:
          service: 'whatsapp'
          
  - job_name: 'vigia-webhook'
    static_configs:
      - targets: ['webhook-server:8000']
        labels:
          service: 'webhook'
          
  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
        labels:
          service: 'cache'
"""
    
    config_path = Path(__file__).parent.parent / "monitoring" / "prometheus.yml"
    config_path.write_text(prometheus_config.strip())
    print(f"✓ Created Prometheus config: {config_path}")

def create_logging_config():
    """Create structured logging configuration"""
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
            },
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "standard",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": "logs/vigia.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json",
                "filename": "logs/errors.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            }
        },
        "loggers": {
            "vigia_detect": {
                "level": "INFO",
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            }
        },
        "root": {
            "level": "INFO",
            "handlers": ["console", "file"]
        }
    }
    
    config_path = Path(__file__).parent.parent / "logging_config.json"
    with open(config_path, 'w') as f:
        json.dump(logging_config, f, indent=2)
    print(f"✓ Created logging config: {config_path}")

def create_grafana_dashboard():
    """Create basic Grafana dashboard for Vigia"""
    dashboard = {
        "dashboard": {
            "title": "Vigia Medical Detection System",
            "panels": [
                {
                    "id": 1,
                    "title": "Detection Rate",
                    "type": "graph",
                    "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8}
                },
                {
                    "id": 2,
                    "title": "Response Time",
                    "type": "graph",
                    "gridPos": {"x": 12, "y": 0, "w": 12, "h": 8}
                },
                {
                    "id": 3,
                    "title": "Redis Cache Hit Rate",
                    "type": "stat",
                    "gridPos": {"x": 0, "y": 8, "w": 6, "h": 4}
                },
                {
                    "id": 4,
                    "title": "Active WhatsApp Sessions",
                    "type": "stat",
                    "gridPos": {"x": 6, "y": 8, "w": 6, "h": 4}
                },
                {
                    "id": 5,
                    "title": "Webhook Delivery Success",
                    "type": "stat",
                    "gridPos": {"x": 12, "y": 8, "w": 6, "h": 4}
                },
                {
                    "id": 6,
                    "title": "Error Rate",
                    "type": "stat",
                    "gridPos": {"x": 18, "y": 8, "w": 6, "h": 4}
                }
            ],
            "refresh": "5s",
            "time": {"from": "now-1h", "to": "now"},
            "version": 1
        },
        "overwrite": True
    }
    
    dashboard_path = Path(__file__).parent.parent / "monitoring" / "grafana" / "dashboards" / "vigia-dashboard.json"
    with open(dashboard_path, 'w') as f:
        json.dump(dashboard, f, indent=2)
    print(f"✓ Created Grafana dashboard: {dashboard_path}")

def create_env_template():
    """Create environment variable template"""
    env_template = """# Vigia v1.0.0-rc1 Environment Configuration

# API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key
GOOGLE_CLOUD_PROJECT=your_gcp_project_id

# Database
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Redis
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=

# WhatsApp (Twilio)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

# Slack
SLACK_BOT_TOKEN=your_slack_bot_token
SLACK_APP_TOKEN=your_slack_app_token

# Webhook Configuration
WEBHOOK_ENABLED=false
WEBHOOK_URL=https://your-webhook-endpoint.com/webhook
WEBHOOK_API_KEY=your_webhook_api_key
WEBHOOK_SECRET=your_webhook_secret

# Monitoring
LOG_LEVEL=INFO
SENTRY_DSN=your_sentry_dsn_if_using_sentry

# Grafana (for docker-compose)
GRAFANA_PASSWORD=admin

# Performance Monitoring (optional)
ENABLE_CODECARBON=false
ENABLE_PYSPY=false
"""
    
    template_path = Path(__file__).parent.parent / ".env.template"
    template_path.write_text(env_template.strip())
    print(f"✓ Created environment template: {template_path}")

def main():
    """Main setup function"""
    print("🚀 Setting up Vigia v1.0.0-rc1 Monitoring")
    print("=" * 50)
    
    create_monitoring_structure()
    create_prometheus_config()
    create_logging_config()
    create_grafana_dashboard()
    create_env_template()
    
    print("\n✅ Monitoring setup completed!")
    print("\nNext steps:")
    print("1. Copy .env.template to .env.production and fill in your values")
    print("2. Run ./scripts/deploy.sh production to deploy")
    print("3. Access Grafana at http://localhost:3000 (with --profile monitoring)")
    print("4. Access Prometheus at http://localhost:9090 (with --profile monitoring)")

if __name__ == "__main__":
    main()