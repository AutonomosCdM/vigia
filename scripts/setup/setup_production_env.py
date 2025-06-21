#!/usr/bin/env python3
"""
Production Environment Setup for Vigia Medical AI System
Automated setup with secure key generation and validation
"""

import os
import sys
import shutil
from pathlib import Path
from typing import Dict, Optional, List
import json
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.setup.secure_key_generator import SecureKeyGenerator


class ProductionEnvSetup:
    """Production environment setup with security validation"""
    
    def __init__(self, project_root: Path = None):
        """Initialize setup manager"""
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.config_dir = self.project_root / "config"
        self.secrets_dir = self.project_root / "secrets"
        self.key_generator = SecureKeyGenerator()
        
    def create_production_env(self, platform: str = "hospital") -> Path:
        """
        Create production .env file with secure keys
        
        Args:
            platform: Deployment platform (hospital, cloud-run, render)
            
        Returns:
            Path to created .env file
        """
        # Generate secure keys
        secure_keys = self.key_generator.generate_complete_env_keys()
        
        # Load base environment template
        env_example_path = self.config_dir / ".env.example"
        if not env_example_path.exists():
            raise FileNotFoundError(f"Template not found: {env_example_path}")
        
        # Read template
        with open(env_example_path, 'r') as f:
            template_content = f.read()
        
        # Platform-specific configurations
        platform_configs = {
            "hospital": {
                "ENVIRONMENT": "production",
                "DEPLOYMENT_PLATFORM": "hospital",
                "REDIS_URL": "redis://vigia-redis:6379",
                "DATABASE_URL": "postgresql://vigia_user:${POSTGRES_PASSWORD}@vigia-postgres:5432/vigia_medical",
                "LOG_LEVEL": "INFO",
                "RATE_LIMIT_ENABLED": "true",
                "RATE_LIMIT_PER_MINUTE": "100",
                "PHI_PROTECTION_ENABLED": "true",
                "MEDICAL_COMPLIANCE_LEVEL": "hipaa",
                "AUDIT_LOGGING_ENABLED": "true"
            },
            "cloud-run": {
                "ENVIRONMENT": "production",
                "DEPLOYMENT_PLATFORM": "cloud-run",
                "LOG_LEVEL": "INFO",
                "RATE_LIMIT_ENABLED": "true",
                "RATE_LIMIT_PER_MINUTE": "200",
                "PHI_PROTECTION_ENABLED": "true",
                "MEDICAL_COMPLIANCE_LEVEL": "hipaa",
                "AUDIT_LOGGING_ENABLED": "true",
                "GOOGLE_CLOUD_PROJECT": "${GOOGLE_CLOUD_PROJECT}",
                "GOOGLE_CLOUD_REGION": "${GOOGLE_CLOUD_REGION}"
            },
            "render": {
                "ENVIRONMENT": "production",
                "DEPLOYMENT_PLATFORM": "render",
                "LOG_LEVEL": "INFO",
                "RATE_LIMIT_ENABLED": "true",
                "RATE_LIMIT_PER_MINUTE": "150",
                "PHI_PROTECTION_ENABLED": "true",
                "MEDICAL_COMPLIANCE_LEVEL": "hipaa",
                "AUDIT_LOGGING_ENABLED": "true"
            }
        }
        
        # Merge secure keys with platform config
        all_vars = {**secure_keys, **platform_configs.get(platform, {})}
        
        # Replace template placeholders
        env_content = template_content
        for key, value in all_vars.items():
            placeholder = f"your-{key.lower().replace('_', '-')}"
            env_content = env_content.replace(placeholder, str(value))
            
            # Also replace direct key references
            if f"{key}=" in env_content:
                lines = env_content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith(f"{key}="):
                        lines[i] = f"{key}={value}"
                env_content = '\n'.join(lines)
            else:
                # Add new keys that aren't in template
                env_content += f"\n{key}={value}"
        
        # Create output file
        output_path = self.config_dir / f".env.{platform}.production"
        with open(output_path, 'w') as f:
            f.write(env_content)
        
        # Set restrictive permissions
        os.chmod(output_path, 0o600)
        
        print(f"✅ Production environment created: {output_path}")
        return output_path
    
    def create_docker_secrets(self, platform: str = "hospital") -> Path:
        """
        Create Docker secrets directory structure
        
        Args:
            platform: Deployment platform
            
        Returns:
            Path to secrets directory
        """
        secrets_dir = self.project_root / "secrets" / platform
        secrets_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate secure keys
        secure_keys = self.key_generator.generate_complete_env_keys()
        
        # Create individual secret files for Docker
        secret_mappings = {
            "postgres_user": "vigia_medical_user",
            "postgres_password": secure_keys["POSTGRES_PASSWORD"],
            "redis_password": secure_keys["REDIS_PASSWORD"],
            "jwt_secret": secure_keys["JWT_SECRET_KEY"],
            "encryption_key": secure_keys["ENCRYPTION_KEY"],
            "phi_encryption_key": secure_keys["PHI_ENCRYPTION_KEY"],
            "audit_signing_key": secure_keys["AUDIT_SIGNING_KEY"],
            "slack_signing": secure_keys["SLACK_SIGNING_SECRET"],
            "webhook_secret": secure_keys["WEBHOOK_SECRET"],
            "vigia_api_key": secure_keys["VIGIA_API_KEY"],
            "mcp_gateway_key": secure_keys["MCP_GATEWAY_KEY"]
        }
        
        for secret_name, secret_value in secret_mappings.items():
            secret_file = secrets_dir / secret_name
            with open(secret_file, 'w') as f:
                f.write(secret_value)
            os.chmod(secret_file, 0o600)
        
        # Create secrets index for reference
        secrets_index = {
            "created_at": str(Path(__file__).stat().st_mtime),
            "platform": platform,
            "secrets": list(secret_mappings.keys()),
            "description": "Docker secrets for Vigia Medical AI production deployment"
        }
        
        with open(secrets_dir / "secrets_index.json", 'w') as f:
            json.dump(secrets_index, f, indent=2)
        
        print(f"✅ Docker secrets created in: {secrets_dir}")
        return secrets_dir
    
    def create_kubernetes_secrets(self) -> Path:
        """
        Create Kubernetes secrets YAML
        
        Returns:
            Path to secrets YAML file
        """
        import base64
        
        # Generate secure keys
        secure_keys = self.key_generator.generate_complete_env_keys()
        
        # Encode secrets for Kubernetes
        k8s_secrets = {}
        for key, value in secure_keys.items():
            k8s_secrets[key.lower()] = base64.b64encode(value.encode()).decode()
        
        # Create Kubernetes secret manifest
        k8s_manifest = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": "vigia-medical-secrets",
                "namespace": "vigia-medical",
                "labels": {
                    "app": "vigia",
                    "component": "secrets",
                    "version": "v1.4.1"
                }
            },
            "type": "Opaque",
            "data": k8s_secrets
        }
        
        # Save to file
        output_path = self.project_root / "deploy" / "kubernetes" / "secrets.yaml"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            yaml.dump(k8s_manifest, f, default_flow_style=False)
        
        print(f"✅ Kubernetes secrets created: {output_path}")
        return output_path
    
    def validate_environment(self, env_file: Path) -> List[str]:
        """
        Validate production environment file
        
        Args:
            env_file: Path to environment file
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if not env_file.exists():
            errors.append(f"Environment file not found: {env_file}")
            return errors
        
        # Read environment variables
        env_vars = {}
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
        
        # Required variables for medical production
        required_vars = [
            "VIGIA_A2A_SECRET_KEY",
            "JWT_SECRET_KEY", 
            "ENCRYPTION_KEY",
            "PHI_ENCRYPTION_KEY",
            "POSTGRES_PASSWORD",
            "AUDIT_SIGNING_KEY",
            "ENVIRONMENT",
            "PHI_PROTECTION_ENABLED",
            "MEDICAL_COMPLIANCE_LEVEL"
        ]
        
        # Check required variables
        for var in required_vars:
            if var not in env_vars:
                errors.append(f"Missing required variable: {var}")
            elif not env_vars[var] or env_vars[var].startswith('your-'):
                errors.append(f"Variable not set properly: {var}")
        
        # Validate key strengths
        key_vars = [
            "VIGIA_A2A_SECRET_KEY",
            "JWT_SECRET_KEY",
            "AUDIT_SIGNING_KEY"
        ]
        
        for var in key_vars:
            if var in env_vars:
                is_strong, entropy = self.key_generator.validate_key_strength(env_vars[var])
                if not is_strong:
                    errors.append(f"Weak key detected for {var} (entropy: {entropy:.2f})")
        
        # Check production settings
        if env_vars.get("ENVIRONMENT") != "production":
            errors.append("ENVIRONMENT must be set to 'production'")
        
        if env_vars.get("PHI_PROTECTION_ENABLED") != "true":
            errors.append("PHI_PROTECTION_ENABLED must be 'true' for medical production")
        
        if env_vars.get("MEDICAL_COMPLIANCE_LEVEL") not in ["hipaa", "minsal", "iso13485"]:
            errors.append("MEDICAL_COMPLIANCE_LEVEL must be set to valid compliance standard")
        
        return errors
    
    def setup_complete_production(self, platform: str = "hospital") -> Dict[str, Path]:
        """
        Complete production setup
        
        Args:
            platform: Deployment platform
            
        Returns:
            Dictionary of created files
        """
        print(f"🏥 Setting up production environment for {platform}...")
        
        created_files = {}
        
        # Create production .env file
        env_file = self.create_production_env(platform)
        created_files["env_file"] = env_file
        
        # Create Docker secrets
        secrets_dir = self.create_docker_secrets(platform)
        created_files["secrets_dir"] = secrets_dir
        
        # Create Kubernetes secrets (if needed)
        if platform in ["cloud-run", "kubernetes"]:
            k8s_secrets = self.create_kubernetes_secrets()
            created_files["k8s_secrets"] = k8s_secrets
        
        # Validate setup
        errors = self.validate_environment(env_file)
        if errors:
            print("❌ Validation errors found:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("✅ All validations passed")
        
        print(f"\n🔒 Production setup complete for {platform}")
        print("Next steps:")
        print(f"1. Review generated files in {self.config_dir}")
        print(f"2. Deploy using: ./scripts/deployment/{platform}-deploy.sh")
        print("3. Verify all services are healthy")
        print("4. Run security validation tests")
        
        return created_files


def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Setup production environment for Vigia Medical AI"
    )
    parser.add_argument(
        '--platform',
        choices=['hospital', 'cloud-run', 'render', 'kubernetes'],
        default='hospital',
        help='Deployment platform'
    )
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate existing environment'
    )
    parser.add_argument(
        '--env-file',
        type=str,
        help='Environment file to validate'
    )
    
    args = parser.parse_args()
    
    setup = ProductionEnvSetup()
    
    if args.validate_only:
        if args.env_file:
            env_path = Path(args.env_file)
        else:
            env_path = setup.config_dir / f".env.{args.platform}.production"
        
        errors = setup.validate_environment(env_path)
        if errors:
            print("❌ Validation errors:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
        else:
            print("✅ Environment validation passed")
    else:
        setup.setup_complete_production(args.platform)


if __name__ == "__main__":
    main()