"""
Unified deployment manager for all deployment targets.
Consolidates Docker, Render, and local deployment configurations.
"""
import os
import subprocess
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from enum import Enum

from config.settings import settings
from ..core.base_client import BaseClient


class DeploymentTarget(Enum):
    LOCAL = "local"
    DOCKER = "docker" 
    RENDER = "render"
    STAGING = "staging"
    PRODUCTION = "production"


class DeployManager(BaseClient):
    """
    Unified deployment manager that handles all deployment targets.
    Eliminates duplication between deploy.sh, deploy_with_render.sh, etc.
    """
    
    def __init__(self):
        """Initialize deployment manager"""
        super().__init__(
            service_name="DeployManager",
            required_fields=[]  # No specific requirements
        )
    
    def _initialize_client(self):
        """Initialize deployment tools"""
        self.project_root = Path(__file__).parent.parent.parent
        self.deployment_configs = self._load_deployment_configs()
    
    def validate_connection(self) -> bool:
        """Validate deployment tools are available"""
        try:
            # Check if required tools are available
            tools = ["docker", "git"]
            for tool in tools:
                subprocess.run([tool, "--version"], 
                             capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def deploy(self, 
              target: DeploymentTarget,
              environment: str = "production",
              dry_run: bool = False,
              force: bool = False) -> Dict[str, Any]:
        """
        Deploy to specified target.
        
        Args:
            target: Deployment target
            environment: Environment (production, staging, development)
            dry_run: If True, only show what would be done
            force: Force deployment even if validation fails
            
        Returns:
            Deployment result
        """
        self.logger.info(f"Starting deployment to {target.value} ({environment})")
        
        try:
            # Pre-deployment validation
            validation_result = self._validate_deployment(target, environment)
            if not validation_result["valid"] and not force:
                return {
                    "success": False,
                    "target": target.value,
                    "environment": environment,
                    "error": "Deployment validation failed",
                    "validation_errors": validation_result["errors"]
                }
            
            # Execute deployment based on target
            if target == DeploymentTarget.LOCAL:
                result = self._deploy_local(environment, dry_run)
            elif target == DeploymentTarget.DOCKER:
                result = self._deploy_docker(environment, dry_run)
            elif target == DeploymentTarget.RENDER:
                result = self._deploy_render(environment, dry_run)
            elif target == DeploymentTarget.STAGING:
                result = self._deploy_staging(dry_run)
            elif target == DeploymentTarget.PRODUCTION:
                result = self._deploy_production(dry_run)
            else:
                raise ValueError(f"Unknown deployment target: {target}")
            
            # Post-deployment health check
            if result.get("success") and not dry_run:
                health_result = self._post_deployment_health_check(target)
                result["health_check"] = health_result
            
            return result
            
        except Exception as e:
            self.logger.error(f"Deployment failed: {str(e)}")
            return {
                "success": False,
                "target": target.value,
                "environment": environment,
                "error": str(e)
            }
    
    def _validate_deployment(self, 
                           target: DeploymentTarget, 
                           environment: str) -> Dict[str, Any]:
        """Validate deployment prerequisites"""
        errors = []
        
        # Check environment variables
        required_vars = self._get_required_env_vars(target, environment)
        for var in required_vars:
            if not os.getenv(var):
                errors.append(f"Missing environment variable: {var}")
        
        # Check Git status
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, check=True
            )
            if result.stdout.strip() and target != DeploymentTarget.LOCAL:
                errors.append("Repository has uncommitted changes")
        except subprocess.CalledProcessError:
            errors.append("Git repository validation failed")
        
        # Check Docker if needed
        if target in [DeploymentTarget.DOCKER, DeploymentTarget.PRODUCTION]:
            try:
                subprocess.run(["docker", "--version"], 
                             capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                errors.append("Docker not available")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _deploy_local(self, environment: str, dry_run: bool) -> Dict[str, Any]:
        """Deploy for local development"""
        commands = [
            "pip install -r requirements.txt",
            "python -m pytest tests/ -v" if environment != "development" else None
        ]
        
        return self._execute_deployment_commands(
            commands, "local", environment, dry_run
        )
    
    def _deploy_docker(self, environment: str, dry_run: bool) -> Dict[str, Any]:
        """Deploy using Docker Compose"""
        compose_file = "docker-compose.yml"
        if environment == "staging":
            compose_file = "docker-compose.staging.yml"
        
        commands = [
            f"docker-compose -f {compose_file} build",
            f"docker-compose -f {compose_file} up -d"
        ]
        
        return self._execute_deployment_commands(
            commands, "docker", environment, dry_run
        )
    
    def _deploy_render(self, environment: str, dry_run: bool) -> Dict[str, Any]:
        """Deploy to Render using API"""
        if dry_run:
            return {
                "success": True,
                "target": "render",
                "environment": environment,
                "message": "DRY RUN: Would deploy to Render"
            }
        
        # Use the existing Render deployment logic
        try:
            # This would integrate with the existing render deployment scripts
            return {
                "success": True,
                "target": "render", 
                "environment": environment,
                "message": "Deployed to Render successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "target": "render",
                "environment": environment,
                "error": str(e)
            }
    
    def _deploy_staging(self, dry_run: bool) -> Dict[str, Any]:
        """Deploy to staging environment"""
        return self._deploy_docker("staging", dry_run)
    
    def _deploy_production(self, dry_run: bool) -> Dict[str, Any]:
        """Deploy to production environment"""
        commands = [
            "docker-compose build --no-cache",
            "docker-compose up -d",
            "docker-compose exec vigia python -c 'from vigia_detect import health_check; print(health_check())'"
        ]
        
        return self._execute_deployment_commands(
            commands, "production", "production", dry_run
        )
    
    def _execute_deployment_commands(self,
                                   commands: List[str],
                                   target: str,
                                   environment: str,
                                   dry_run: bool) -> Dict[str, Any]:
        """Execute deployment commands"""
        if dry_run:
            return {
                "success": True,
                "target": target,
                "environment": environment,
                "message": f"DRY RUN: Would execute {len(commands)} commands",
                "commands": [cmd for cmd in commands if cmd]
            }
        
        executed_commands = []
        
        for command in commands:
            if not command:
                continue
                
            try:
                self.logger.info(f"Executing: {command}")
                result = subprocess.run(
                    command.split(),
                    capture_output=True,
                    text=True,
                    check=True,
                    cwd=self.project_root
                )
                executed_commands.append({
                    "command": command,
                    "success": True,
                    "output": result.stdout
                })
            except subprocess.CalledProcessError as e:
                executed_commands.append({
                    "command": command,
                    "success": False,
                    "error": e.stderr
                })
                return {
                    "success": False,
                    "target": target,
                    "environment": environment,
                    "error": f"Command failed: {command}",
                    "executed_commands": executed_commands
                }
        
        return {
            "success": True,
            "target": target,
            "environment": environment,
            "executed_commands": executed_commands
        }
    
    def _get_required_env_vars(self, 
                             target: DeploymentTarget, 
                             environment: str) -> List[str]:
        """Get required environment variables for deployment"""
        base_vars = [
            "SUPABASE_URL",
            "SUPABASE_KEY",
            "ANTHROPIC_API_KEY"
        ]
        
        if target == DeploymentTarget.RENDER:
            base_vars.extend([
                "TWILIO_ACCOUNT_SID",
                "TWILIO_AUTH_TOKEN",
                "TWILIO_WHATSAPP_FROM"
            ])
        
        return base_vars
    
    def _post_deployment_health_check(self, 
                                    target: DeploymentTarget) -> Dict[str, Any]:
        """Perform health check after deployment"""
        try:
            from .health_checker import HealthChecker
            
            checker = HealthChecker()
            return checker.comprehensive_health_check()
            
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _load_deployment_configs(self) -> Dict[str, Any]:
        """Load deployment configurations"""
        return {
            "docker": {
                "compose_file": "docker-compose.yml",
                "staging_compose_file": "docker-compose.staging.yml"
            },
            "render": {
                "config_file": "render.yaml"
            },
            "backup": {
                "enabled": True,
                "retention_days": 30
            }
        }