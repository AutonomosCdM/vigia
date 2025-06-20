"""
Health checker for Vigia medical detection system.
Provides comprehensive health monitoring for all system components.
"""
import asyncio
import aiohttp
import redis
from typing import Dict, Any, List, Optional
from datetime import datetime
import subprocess

from config.settings import settings
from ..core.base_client import BaseClient


class HealthChecker(BaseClient):
    """
    Comprehensive health checker for all Vigia system components.
    """
    
    def __init__(self):
        """Initialize health checker"""
        super().__init__(
            service_name="HealthChecker",
            required_fields=[]
        )
    
    def _initialize_client(self):
        """Initialize health checking components"""
        self.timeout = 30  # seconds
        self.checks_registry = {
            "database": self._check_database,
            "redis": self._check_redis,
            "external_apis": self._check_external_apis,
            "file_system": self._check_file_system,
            "services": self._check_services,
            "system_resources": self._check_system_resources
        }
    
    def validate_connection(self) -> bool:
        """Validate health checker is ready"""
        return True
    
    def comprehensive_health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check of all system components.
        
        Returns:
            Complete health status report
        """
        health_report = {
            "overall_status": "unknown",
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "summary": {
                "total_checks": 0,
                "passed_checks": 0,
                "failed_checks": 0,
                "warning_checks": 0
            }
        }
        
        # Run all health checks
        for check_name, check_function in self.checks_registry.items():
            try:
                self.logger.info(f"Running health check: {check_name}")
                check_result = check_function()
                health_report["checks"][check_name] = check_result
                
                # Update summary
                health_report["summary"]["total_checks"] += 1
                status = check_result.get("status", "failed")
                
                if status == "healthy":
                    health_report["summary"]["passed_checks"] += 1
                elif status == "warning":
                    health_report["summary"]["warning_checks"] += 1
                else:
                    health_report["summary"]["failed_checks"] += 1
                    
            except Exception as e:
                self.logger.error(f"Health check {check_name} failed: {str(e)}")
                health_report["checks"][check_name] = {
                    "status": "failed",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                health_report["summary"]["total_checks"] += 1
                health_report["summary"]["failed_checks"] += 1
        
        # Determine overall status
        if health_report["summary"]["failed_checks"] == 0:
            if health_report["summary"]["warning_checks"] == 0:
                health_report["overall_status"] = "healthy"
            else:
                health_report["overall_status"] = "warning"
        else:
            health_report["overall_status"] = "unhealthy"
        
        return health_report
    
    def _check_database(self) -> Dict[str, Any]:
        """Check Supabase database connectivity"""
        try:
            from ..db import SupabaseClient
            
            start_time = datetime.now()
            client = SupabaseClient()
            
            # Test basic connectivity
            is_connected = client.validate_connection()
            response_time = (datetime.now() - start_time).total_seconds()
            
            if is_connected:
                return {
                    "status": "healthy",
                    "response_time_seconds": response_time,
                    "message": "Database connection successful",
                    "details": {
                        "url": settings.supabase_url,
                        "connection_test": "passed"
                    }
                }
            else:
                return {
                    "status": "failed",
                    "response_time_seconds": response_time,
                    "message": "Database connection failed",
                    "details": {
                        "url": settings.supabase_url,
                        "connection_test": "failed"
                    }
                }
                
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "message": "Database health check failed"
            }
    
    def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity and performance"""
        try:
            start_time = datetime.now()
            
            # Connect to Redis
            redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                decode_responses=True,
                socket_timeout=10
            )
            
            # Test basic operations
            redis_client.ping()
            
            # Test set/get operation
            test_key = "health_check_test"
            test_value = "test_value"
            redis_client.set(test_key, test_value, ex=60)
            retrieved_value = redis_client.get(test_key)
            redis_client.delete(test_key)
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            if retrieved_value == test_value:
                # Get Redis info
                info = redis_client.info()
                
                return {
                    "status": "healthy",
                    "response_time_seconds": response_time,
                    "message": "Redis connection and operations successful",
                    "details": {
                        "version": info.get("redis_version"),
                        "used_memory_human": info.get("used_memory_human"),
                        "connected_clients": info.get("connected_clients"),
                        "operations_test": "passed"
                    }
                }
            else:
                return {
                    "status": "failed",
                    "response_time_seconds": response_time,
                    "message": "Redis operations test failed"
                }
                
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "message": "Redis health check failed"
            }
    
    def _check_external_apis(self) -> Dict[str, Any]:
        """Check external API connectivity"""
        api_checks = {}
        overall_status = "healthy"
        
        # Check Anthropic API
        try:
            # Simple test - just check if we have the API key configured
            if settings.anthropic_api_key:
                api_checks["anthropic"] = {
                    "status": "configured",
                    "message": "API key configured"
                }
            else:
                api_checks["anthropic"] = {
                    "status": "warning",
                    "message": "API key not configured"
                }
                overall_status = "warning"
        except Exception as e:
            api_checks["anthropic"] = {
                "status": "failed",
                "error": str(e)
            }
            overall_status = "failed"
        
        # Check Twilio (if configured)
        try:
            if hasattr(settings, 'twilio_account_sid') and settings.twilio_account_sid:
                api_checks["twilio"] = {
                    "status": "configured",
                    "message": "Twilio credentials configured"
                }
            else:
                api_checks["twilio"] = {
                    "status": "warning",
                    "message": "Twilio not configured"
                }
        except Exception as e:
            api_checks["twilio"] = {
                "status": "failed",
                "error": str(e)
            }
        
        return {
            "status": overall_status,
            "message": f"External APIs check completed",
            "details": api_checks
        }
    
    def _check_file_system(self) -> Dict[str, Any]:
        """Check file system access and permissions"""
        try:
            import tempfile
            import os
            from pathlib import Path
            
            checks = {}
            overall_status = "healthy"
            
            # Check temp directory access
            try:
                with tempfile.NamedTemporaryFile(delete=True) as tmp:
                    tmp.write(b"health_check_test")
                    tmp.flush()
                checks["temp_directory"] = {"status": "healthy", "message": "Temp directory accessible"}
            except Exception as e:
                checks["temp_directory"] = {"status": "failed", "error": str(e)}
                overall_status = "failed"
            
            # Check data directories
            data_dirs = ["./data", "./logs", "./models"]
            for dir_path in data_dirs:
                path = Path(dir_path)
                if path.exists():
                    if os.access(path, os.R_OK | os.W_OK):
                        checks[f"directory_{dir_path}"] = {
                            "status": "healthy",
                            "message": f"Directory {dir_path} accessible"
                        }
                    else:
                        checks[f"directory_{dir_path}"] = {
                            "status": "failed",
                            "message": f"Directory {dir_path} not accessible"
                        }
                        overall_status = "failed"
                else:
                    checks[f"directory_{dir_path}"] = {
                        "status": "warning",
                        "message": f"Directory {dir_path} does not exist"
                    }
                    if overall_status == "healthy":
                        overall_status = "warning"
            
            return {
                "status": overall_status,
                "message": "File system check completed",
                "details": checks
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "message": "File system health check failed"
            }
    
    def _check_services(self) -> Dict[str, Any]:
        """Check if required services are running"""
        try:
            services = {}
            
            # Check if we're in a Docker environment
            in_docker = Path("/.dockerenv").exists()
            services["docker_environment"] = {
                "status": "detected" if in_docker else "not_detected",
                "message": f"Running {'in' if in_docker else 'outside'} Docker"
            }
            
            # Check Python version
            import sys
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            services["python"] = {
                "status": "healthy",
                "version": python_version,
                "message": f"Python {python_version} running"
            }
            
            return {
                "status": "healthy",
                "message": "Services check completed",
                "details": services
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "message": "Services health check failed"
            }
    
    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            import psutil
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            status = "healthy"
            warnings = []
            
            # Check CPU usage
            if cpu_percent > 90:
                status = "warning"
                warnings.append(f"High CPU usage: {cpu_percent}%")
            
            # Check memory usage
            if memory.percent > 90:
                status = "warning"
                warnings.append(f"High memory usage: {memory.percent}%")
            
            # Check disk usage
            if disk.percent > 90:
                status = "warning"
                warnings.append(f"High disk usage: {disk.percent}%")
            
            return {
                "status": status,
                "message": "System resources check completed",
                "warnings": warnings,
                "details": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": round(memory.available / (1024**3), 2),
                    "disk_percent": disk.percent,
                    "disk_free_gb": round(disk.free / (1024**3), 2)
                }
            }
            
        except ImportError:
            return {
                "status": "warning",
                "message": "psutil not available, system metrics not collected"
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "message": "System resources health check failed"
            }
    
    def quick_health_check(self) -> Dict[str, Any]:
        """
        Perform a quick health check of critical components only.
        
        Returns:
            Quick health status
        """
        critical_checks = ["database", "redis"]
        
        quick_report = {
            "overall_status": "unknown",
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "check_type": "quick"
        }
        
        failed_checks = 0
        
        for check_name in critical_checks:
            if check_name in self.checks_registry:
                try:
                    check_result = self.checks_registry[check_name]()
                    quick_report["checks"][check_name] = check_result
                    
                    if check_result.get("status") != "healthy":
                        failed_checks += 1
                        
                except Exception as e:
                    quick_report["checks"][check_name] = {
                        "status": "failed",
                        "error": str(e)
                    }
                    failed_checks += 1
        
        quick_report["overall_status"] = "healthy" if failed_checks == 0 else "unhealthy"
        
        return quick_report