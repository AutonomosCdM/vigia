"""
Configuration manager for Vigia deployment.
Handles environment-specific configurations and validation.
"""
import os
import json
import yaml
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from enum import Enum

from config.settings import settings
from ..core.base_client import BaseClient
from ..utils.shared_utilities import VigiaValidator


class EnvironmentType(Enum):
    """Supported environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class ConfigManager(BaseClient):
    """
    Configuration manager for deployment and environment setup.
    Handles validation and generation of configuration files.
    """
    
    def __init__(self):
        """Initialize configuration manager"""
        super().__init__(
            service_name="ConfigManager",
            required_fields=[]
        )
    
    def _initialize_client(self):
        """Initialize configuration management"""
        self.project_root = Path(__file__).parent.parent.parent
        self.config_templates = self._load_config_templates()
    
    def validate_connection(self) -> bool:
        """Validate configuration manager is ready"""
        return True
    
    def validate_environment_config(self, 
                                  environment: EnvironmentType) -> Dict[str, Any]:
        """
        Validate configuration for a specific environment.
        
        Args:
            environment: Environment type to validate
            
        Returns:
            Validation result with details
        """
        validation_result = {
            "valid": True,
            "environment": environment.value,
            "errors": [],
            "warnings": [],
            "missing_variables": [],
            "timestamp": settings.environment
        }
        
        # Get required variables for environment
        required_vars = self._get_required_variables(environment)
        
        # Check each required variable
        for var_name, var_info in required_vars.items():
            value = getattr(settings, var_name, None)
            
            if value is None:
                validation_result["errors"].append(f"Missing required variable: {var_name}")
                validation_result["missing_variables"].append(var_name)
                validation_result["valid"] = False
            else:
                # Validate variable format if validator is specified
                if "validator" in var_info:
                    validator_result = var_info["validator"](value)
                    if not validator_result.get("valid", True):
                        validation_result["errors"].append(
                            f"Invalid {var_name}: {validator_result.get('error', 'Format error')}"
                        )
                        validation_result["valid"] = False
        
        # Check optional but recommended variables
        optional_vars = self._get_optional_variables(environment)
        for var_name in optional_vars:
            value = getattr(settings, var_name, None)
            if value is None:
                validation_result["warnings"].append(f"Optional variable not set: {var_name}")
        
        # Environment-specific validations
        if environment == EnvironmentType.PRODUCTION:
            self._validate_production_config(validation_result)
        elif environment == EnvironmentType.STAGING:
            self._validate_staging_config(validation_result)
        
        return validation_result
    
    def generate_docker_config(self, 
                             environment: EnvironmentType,
                             services: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate Docker configuration for specified environment.
        
        Args:
            environment: Target environment
            services: List of services to include (None for all)
            
        Returns:
            Docker configuration
        """
        base_config = {
            "version": "3.8",
            "services": {},
            "volumes": {},
            "networks": {
                "vigia-network": {"driver": "bridge"}
            }
        }
        
        # Define available services
        available_services = {
            "vigia": self._get_vigia_service_config(environment),
            "whatsapp": self._get_whatsapp_service_config(environment),
            "webhook": self._get_webhook_service_config(environment),
            "slack": self._get_slack_service_config(environment),
            "redis": self._get_redis_service_config(environment)
        }
        
        # Add monitoring services for production
        if environment == EnvironmentType.PRODUCTION:
            available_services.update({
                "prometheus": self._get_prometheus_service_config(),
                "grafana": self._get_grafana_service_config()
            })
        
        # Select services to include
        if services is None:
            services = list(available_services.keys())
        
        for service_name in services:
            if service_name in available_services:
                base_config["services"][service_name] = available_services[service_name]
        
        # Add volumes
        base_config["volumes"] = {
            "redis-data": None,
            "prometheus-data": None,
            "grafana-data": None
        }
        
        return base_config
    
    def generate_render_config(self) -> Dict[str, Any]:
        """
        Generate Render.com deployment configuration.
        
        Returns:
            Render configuration
        """
        return {
            "services": [
                {
                    "type": "web",
                    "name": "vigia-whatsapp",
                    "runtime": "python",
                    "buildCommand": "pip install -r requirements.txt",
                    "startCommand": "python vigia_detect/messaging/whatsapp/server.py",
                    "envVars": self._get_render_env_vars()
                },
                {
                    "type": "web", 
                    "name": "vigia-webhook",
                    "runtime": "python",
                    "buildCommand": "pip install -r requirements.txt",
                    "startCommand": "python -m vigia_detect.webhook.server",
                    "envVars": self._get_render_env_vars(webhook_service=True)
                }
            ]
        }
    
    def generate_env_file(self, 
                         environment: EnvironmentType,
                         output_path: Optional[Path] = None) -> Path:
        """
        Generate .env file for specified environment.
        
        Args:
            environment: Target environment
            output_path: Output file path (optional)
            
        Returns:
            Path to generated .env file
        """
        if output_path is None:
            output_path = self.project_root / f".env.{environment.value}"
        
        env_vars = self._get_env_variables_for_environment(environment)
        
        with open(output_path, 'w') as f:
            f.write(f"# Vigia Environment Configuration - {environment.value.upper()}\n")
            f.write(f"# Generated on {self._get_timestamp()}\n\n")
            
            for category, variables in env_vars.items():
                f.write(f"# {category.upper()}\n")
                for var_name, var_value in variables.items():
                    if var_value is not None:
                        f.write(f"{var_name}={var_value}\n")
                    else:
                        f.write(f"# {var_name}=\n")
                f.write("\n")
        
        return output_path
    
    def _get_required_variables(self, environment: EnvironmentType) -> Dict[str, Dict[str, Any]]:
        """Get required variables for environment with validation rules"""
        base_vars = {
            "supabase_url": {
                "description": "Supabase project URL",
                "validator": lambda x: {"valid": x.startswith("https://")}
            },
            "supabase_key": {
                "description": "Supabase anon key",
                "validator": lambda x: {"valid": len(x) > 50}
            },
            "anthropic_api_key": {
                "description": "Anthropic API key",
                "validator": lambda x: {"valid": x.startswith("sk-")}
            }
        }
        
        if environment in [EnvironmentType.STAGING, EnvironmentType.PRODUCTION]:
            base_vars.update({
                "twilio_account_sid": {
                    "description": "Twilio Account SID",
                    "validator": lambda x: {"valid": x.startswith("AC")}
                },
                "twilio_auth_token": {
                    "description": "Twilio Auth Token",
                    "validator": lambda x: {"valid": len(x) == 32}
                },
                "twilio_whatsapp_from": {
                    "description": "Twilio WhatsApp number",
                    "validator": lambda x: {"valid": x.startswith("whatsapp:")}
                }
            })
        
        return base_vars
    
    def _get_optional_variables(self, environment: EnvironmentType) -> List[str]:
        """Get optional variables for environment"""
        optional = ["slack_bot_token", "webhook_url", "webhook_api_key"]
        
        if environment == EnvironmentType.PRODUCTION:
            optional.extend(["grafana_password", "prometheus_config"])
        
        return optional
    
    def _validate_production_config(self, validation_result: Dict[str, Any]) -> None:
        """Add production-specific validations"""
        # Check for debug mode in production
        if getattr(settings, 'debug', False):
            validation_result["errors"].append("Debug mode should be disabled in production")
            validation_result["valid"] = False
        
        # Check for proper secret key
        secret_key = getattr(settings, 'secret_key', '')
        if len(secret_key) < 32:
            validation_result["errors"].append("Secret key too short for production")
            validation_result["valid"] = False
        
        # Check rate limiting is enabled
        if not getattr(settings, 'rate_limit_enabled', False):
            validation_result["warnings"].append("Rate limiting is not enabled")
    
    def _validate_staging_config(self, validation_result: Dict[str, Any]) -> None:
        """Add staging-specific validations"""
        # Check that staging uses test data
        if not getattr(settings, 'use_mock_yolo', False):
            validation_result["warnings"].append("Consider using mock YOLO in staging")
    
    def _get_vigia_service_config(self, environment: EnvironmentType) -> Dict[str, Any]:
        """Get Vigia main service configuration"""
        config = {
            "build": ".",
            "container_name": f"vigia-detector-{environment.value}",
            "environment": self._get_service_env_vars(),
            "volumes": [
                "./data/input:/app/data/input:ro",
                "./data/output:/app/data/output",
                "./logs:/app/logs"
            ],
            "depends_on": ["redis"],
            "networks": ["vigia-network"],
            "restart": "unless-stopped"
        }
        
        if environment == EnvironmentType.PRODUCTION:
            config.update({
                "security_opt": ["no-new-privileges:true"],
                "cap_drop": ["ALL"],
                "read_only": True,
                "tmpfs": ["/tmp", "/app/temp"]
            })
        
        return config
    
    def _get_whatsapp_service_config(self, environment: EnvironmentType) -> Dict[str, Any]:
        """Get WhatsApp service configuration"""
        port = "5000" if environment == EnvironmentType.PRODUCTION else "5001"
        
        return {
            "build": ".",
            "container_name": f"vigia-whatsapp-{environment.value}",
            "command": ["python", "-m", "vigia_detect.messaging.whatsapp.server"],
            "environment": self._get_service_env_vars(),
            "ports": [f"{port}:5000"],
            "depends_on": ["redis"],
            "networks": ["vigia-network"],
            "restart": "unless-stopped"
        }
    
    def _get_webhook_service_config(self, environment: EnvironmentType) -> Dict[str, Any]:
        """Get webhook service configuration"""
        port = "8000" if environment == EnvironmentType.PRODUCTION else "8001"
        
        return {
            "build": ".",
            "container_name": f"vigia-webhook-{environment.value}",
            "command": ["python", "-m", "vigia_detect.webhook.server"],
            "environment": self._get_service_env_vars(),
            "ports": [f"{port}:8000"],
            "depends_on": ["redis"],
            "networks": ["vigia-network"],
            "restart": "unless-stopped"
        }
    
    def _get_slack_service_config(self, environment: EnvironmentType) -> Dict[str, Any]:
        """Get Slack service configuration"""
        return {
            "build": ".",
            "container_name": f"vigia-slack-{environment.value}",
            "command": ["python", "apps/slack_server_refactored.py"],
            "environment": self._get_service_env_vars(),
            "depends_on": ["redis"],
            "networks": ["vigia-network"],
            "restart": "unless-stopped"
        }
    
    def _get_redis_service_config(self, environment: EnvironmentType) -> Dict[str, Any]:
        """Get Redis service configuration"""
        return {
            "image": "redis:7-alpine",
            "container_name": f"vigia-redis-{environment.value}",
            "command": "redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru",
            "volumes": ["redis-data:/data"],
            "ports": ["6379:6379"],
            "networks": ["vigia-network"],
            "restart": "unless-stopped",
            "healthcheck": {
                "test": ["CMD", "redis-cli", "ping"],
                "interval": "5s",
                "timeout": "3s",
                "retries": 5
            }
        }
    
    def _get_prometheus_service_config(self) -> Dict[str, Any]:
        """Get Prometheus service configuration"""
        return {
            "image": "prom/prometheus:latest",
            "container_name": "vigia-prometheus",
            "volumes": [
                "./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml",
                "prometheus-data:/prometheus"
            ],
            "ports": ["9090:9090"],
            "networks": ["vigia-network"],
            "restart": "unless-stopped",
            "profiles": ["monitoring"]
        }
    
    def _get_grafana_service_config(self) -> Dict[str, Any]:
        """Get Grafana service configuration"""
        return {
            "image": "grafana/grafana:latest",
            "container_name": "vigia-grafana",
            "environment": [
                "GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}"
            ],
            "volumes": [
                "grafana-data:/var/lib/grafana",
                "./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards"
            ],
            "ports": ["3000:3000"],
            "networks": ["vigia-network"],
            "restart": "unless-stopped",
            "profiles": ["monitoring"]
        }
    
    def _get_service_env_vars(self) -> List[str]:
        """Get environment variables for services"""
        return [
            "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}",
            "SUPABASE_URL=${SUPABASE_URL}",
            "SUPABASE_KEY=${SUPABASE_KEY}",
            "TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID}",
            "TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN}",
            "TWILIO_WHATSAPP_FROM=${TWILIO_WHATSAPP_FROM}",
            "SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}",
            "REDIS_URL=${REDIS_URL:-redis://redis:6379}",
            "LOG_LEVEL=${LOG_LEVEL:-INFO}",
            "ENVIRONMENT=${ENVIRONMENT:-production}",
            "RATE_LIMIT_ENABLED=${RATE_LIMIT_ENABLED:-false}",
            "WEBHOOK_ENABLED=${WEBHOOK_ENABLED:-false}",
            "WEBHOOK_URL=${WEBHOOK_URL}",
            "WEBHOOK_API_KEY=${WEBHOOK_API_KEY}"
        ]
    
    def _get_render_env_vars(self, webhook_service: bool = False) -> List[Dict[str, Any]]:
        """Get environment variables for Render deployment"""
        base_vars = [
            {"key": "ANTHROPIC_API_KEY", "sync": False},
            {"key": "SUPABASE_URL", "sync": False},
            {"key": "SUPABASE_KEY", "sync": False},
            {"key": "TWILIO_ACCOUNT_SID", "sync": False},
            {"key": "TWILIO_AUTH_TOKEN", "sync": False},
            {"key": "TWILIO_WHATSAPP_FROM", "sync": False},
            {"key": "VIGIA_USE_MOCK_YOLO", "value": "false"}
        ]
        
        if webhook_service:
            base_vars.append({"key": "WEBHOOK_SECRET", "generateValue": True})
        else:
            base_vars.extend([
                {"key": "SLACK_BOT_TOKEN", "sync": False},
                {"key": "SLACK_CHANNEL_ID", "value": "C08TJHZFVD1"}
            ])
        
        return base_vars
    
    def _get_env_variables_for_environment(self, environment: EnvironmentType) -> Dict[str, Dict[str, Any]]:
        """Get environment variables organized by category"""
        return {
            "database": {
                "SUPABASE_URL": getattr(settings, 'supabase_url', None),
                "SUPABASE_KEY": getattr(settings, 'supabase_key', None)
            },
            "ai_services": {
                "ANTHROPIC_API_KEY": getattr(settings, 'anthropic_api_key', None),
                "ANTHROPIC_MODEL": getattr(settings, 'anthropic_model', 'claude-3-sonnet-20240229')
            },
            "messaging": {
                "TWILIO_ACCOUNT_SID": getattr(settings, 'twilio_account_sid', None),
                "TWILIO_AUTH_TOKEN": getattr(settings, 'twilio_auth_token', None),
                "TWILIO_WHATSAPP_FROM": getattr(settings, 'twilio_whatsapp_from', None),
                "SLACK_BOT_TOKEN": getattr(settings, 'slack_bot_token', None)
            },
            "application": {
                "ENVIRONMENT": environment.value,
                "DEBUG": str(environment == EnvironmentType.DEVELOPMENT).lower(),
                "LOG_LEVEL": "DEBUG" if environment == EnvironmentType.DEVELOPMENT else "INFO",
                "USE_MOCK_YOLO": str(environment in [EnvironmentType.DEVELOPMENT, EnvironmentType.TESTING]).lower()
            },
            "redis": {
                "REDIS_HOST": getattr(settings, 'redis_host', 'localhost'),
                "REDIS_PORT": str(getattr(settings, 'redis_port', 6379)),
                "REDIS_PASSWORD": getattr(settings, 'redis_password', None)
            }
        }
    
    def _load_config_templates(self) -> Dict[str, Any]:
        """Load configuration templates"""
        return {
            "docker_compose": "docker-compose template",
            "render": "render template"
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for file headers"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")