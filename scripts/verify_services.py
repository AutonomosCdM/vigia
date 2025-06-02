#!/usr/bin/env python3
"""
Verify all Vigia services are running and healthy for Clinical Dry Run.
"""

import os
import sys
import requests
import redis
import time
from pathlib import Path
from typing import Dict, Any, List
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('service-verifier')


class ServiceVerifier:
    """Verifies all Vigia services are healthy."""
    
    def __init__(self):
        """Initialize service verifier."""
        self.services = {
            "whatsapp": {
                "url": "http://localhost:5001/health",
                "name": "WhatsApp Server",
                "required": True
            },
            "webhook": {
                "url": "http://localhost:8001/health",
                "name": "Webhook Server",
                "required": True
            },
            "redis": {
                "url": "redis://localhost:6380",
                "name": "Redis Cache",
                "required": True
            },
            "prometheus": {
                "url": "http://localhost:9091/-/healthy",
                "name": "Prometheus",
                "required": False
            },
            "grafana": {
                "url": "http://localhost:3001/api/health",
                "name": "Grafana",
                "required": False
            }
        }
        
        self.results = {}
    
    def check_http_service(self, name: str, url: str) -> Dict[str, Any]:
        """Check HTTP service health."""
        try:
            response = requests.get(url, timeout=5)
            healthy = response.status_code == 200
            
            return {
                "healthy": healthy,
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "details": response.json() if healthy and response.headers.get('content-type', '').startswith('application/json') else None
            }
        except requests.exceptions.ConnectionError:
            return {
                "healthy": False,
                "error": "Connection refused - service not running"
            }
        except requests.exceptions.Timeout:
            return {
                "healthy": False,
                "error": "Request timeout"
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    def check_redis(self, url: str) -> Dict[str, Any]:
        """Check Redis service health."""
        try:
            client = redis.from_url(url)
            start_time = time.time()
            client.ping()
            response_time = time.time() - start_time
            
            # Get some stats
            info = client.info()
            
            return {
                "healthy": True,
                "response_time": response_time,
                "details": {
                    "version": info.get("redis_version"),
                    "connected_clients": info.get("connected_clients"),
                    "used_memory_human": info.get("used_memory_human"),
                    "uptime_in_days": info.get("uptime_in_days")
                }
            }
        except redis.ConnectionError:
            return {
                "healthy": False,
                "error": "Connection refused - Redis not running"
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    def verify_all_services(self) -> Dict[str, Any]:
        """Verify all services."""
        logger.info("Verifying Vigia services...")
        
        for service_key, service_info in self.services.items():
            logger.info(f"\nChecking {service_info['name']}...")
            
            if service_key == "redis":
                result = self.check_redis(service_info["url"])
            else:
                result = self.check_http_service(service_key, service_info["url"])
            
            self.results[service_key] = {
                **result,
                "name": service_info["name"],
                "required": service_info["required"]
            }
            
            # Log result
            if result["healthy"]:
                logger.info(f"✓ {service_info['name']} is healthy (response time: {result.get('response_time', 0):.3f}s)")
            else:
                level = logger.error if service_info["required"] else logger.warning
                level(f"✗ {service_info['name']} is not healthy: {result.get('error', 'Unknown error')}")
        
        return self.results
    
    def get_summary(self) -> Dict[str, Any]:
        """Get verification summary."""
        required_healthy = all(
            result["healthy"] 
            for result in self.results.values() 
            if result["required"]
        )
        
        optional_healthy = sum(
            1 for result in self.results.values() 
            if not result["required"] and result["healthy"]
        )
        
        optional_total = sum(
            1 for result in self.results.values() 
            if not result["required"]
        )
        
        return {
            "all_required_healthy": required_healthy,
            "required_services": {
                name: result["healthy"] 
                for name, result in self.results.items() 
                if result["required"]
            },
            "optional_services": {
                name: result["healthy"] 
                for name, result in self.results.items() 
                if not result["required"]
            },
            "optional_healthy_count": optional_healthy,
            "optional_total_count": optional_total
        }
    
    def print_summary(self):
        """Print verification summary."""
        summary = self.get_summary()
        
        print("\n" + "="*60)
        print("SERVICE VERIFICATION SUMMARY")
        print("="*60)
        
        print("\nRequired Services:")
        for service, healthy in summary["required_services"].items():
            status = "✓" if healthy else "✗"
            print(f"  {status} {self.results[service]['name']}")
        
        print("\nOptional Services:")
        for service, healthy in summary["optional_services"].items():
            status = "✓" if healthy else "✗"
            print(f"  {status} {self.results[service]['name']}")
        
        print("\n" + "-"*60)
        
        if summary["all_required_healthy"]:
            print("✅ All required services are healthy - Ready for Clinical Dry Run!")
        else:
            print("❌ Some required services are not healthy - Please check the logs above")
            print("\nTo start services:")
            print("  - WhatsApp: ./start_whatsapp_server.sh")
            print("  - All services: ./scripts/deploy.sh staging")
        
        print("="*60)
    
    def get_service_urls(self) -> Dict[str, str]:
        """Get service URLs for testing."""
        return {
            "whatsapp_webhook": "http://localhost:5001/webhook/whatsapp",
            "webhook_api": "http://localhost:8001/webhook",
            "grafana_dashboard": "http://localhost:3001",
            "prometheus_ui": "http://localhost:9091"
        }


def main():
    """Main function."""
    verifier = ServiceVerifier()
    
    # Verify all services
    verifier.verify_all_services()
    
    # Print summary
    verifier.print_summary()
    
    # If all required services are healthy, print URLs
    summary = verifier.get_summary()
    if summary["all_required_healthy"]:
        print("\nService URLs for testing:")
        urls = verifier.get_service_urls()
        for name, url in urls.items():
            print(f"  {name}: {url}")
    
    # Exit with appropriate code
    sys.exit(0 if summary["all_required_healthy"] else 1)


if __name__ == "__main__":
    main()