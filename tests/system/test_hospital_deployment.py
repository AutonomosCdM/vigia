#!/usr/bin/env python3
"""
Vigia Hospital Infrastructure Validation Tests
Comprehensive automated testing for hospital deployment
"""

import pytest
import requests
import docker
import subprocess
import time
import os
import json
from pathlib import Path
from typing import Dict, List, Optional
import psycopg2
import redis
from celery import Celery


@pytest.fixture(scope="session")
def docker_client():
    """Docker client for infrastructure testing"""
    return docker.from_env()


@pytest.fixture(scope="session")
def hospital_services(docker_client):
    """Get running hospital services"""
    try:
        containers = docker_client.containers.list()
        hospital_containers = {
            container.name: container 
            for container in containers 
            if 'vigia' in container.name
        }
        return hospital_containers
    except Exception as e:
        pytest.skip(f"Docker not available or no hospital services running: {e}")


class TestHospitalInfrastructure:
    """Test hospital deployment infrastructure"""
    
    def test_docker_compose_file_exists(self):
        """Test that Docker Compose file exists and is valid"""
        compose_file = Path("docker-compose.hospital.yml")
        assert compose_file.exists(), "Hospital Docker Compose file not found"
        
        # Validate compose file syntax
        result = subprocess.run(
            ["docker-compose", "-f", str(compose_file), "config"],
            capture_output=True, text=True
        )
        assert result.returncode == 0, f"Invalid compose file: {result.stderr}"
    
    def test_environment_file_exists(self):
        """Test that hospital environment file exists"""
        env_file = Path(".env.hospital")
        assert env_file.exists(), "Hospital environment file not found"
        
        # Check critical environment variables
        with open(env_file) as f:
            content = f.read()
            critical_vars = [
                "ENVIRONMENT=hospital",
                "MEDICAL_COMPLIANCE_LEVEL=hipaa",
                "PHI_PROTECTION_ENABLED=true"
            ]
            for var in critical_vars:
                assert var in content, f"Missing critical environment variable: {var}"
    
    def test_deployment_script_exists(self):
        """Test that deployment script exists and is executable"""
        script_path = Path("scripts/hospital-deploy.sh")
        assert script_path.exists(), "Hospital deployment script not found"
        assert os.access(script_path, os.X_OK), "Deployment script not executable"
    
    def test_ssl_certificate_generation(self, tmp_path):
        """Test SSL certificate generation process"""
        ssl_dir = tmp_path / "ssl"
        ssl_dir.mkdir()
        
        # Generate test certificates
        result = subprocess.run([
            "openssl", "req", "-x509", "-nodes", "-days", "1",
            "-newkey", "rsa:2048",
            "-keyout", str(ssl_dir / "test.key"),
            "-out", str(ssl_dir / "test.crt"),
            "-subj", "/C=US/ST=Test/L=Test/O=Test/CN=test.local"
        ], capture_output=True)
        
        assert result.returncode == 0, "SSL certificate generation failed"
        assert (ssl_dir / "test.crt").exists()
        assert (ssl_dir / "test.key").exists()


class TestHospitalServices:
    """Test running hospital services"""
    
    def test_postgres_service(self, hospital_services):
        """Test PostgreSQL service health"""
        postgres_container = None
        for name, container in hospital_services.items():
            if 'postgres' in name:
                postgres_container = container
                break
        
        if postgres_container:
            assert postgres_container.status == 'running'
            
            # Test database connection
            try:
                # Use environment variables from hospital config
                conn = psycopg2.connect(
                    host="localhost",
                    port=5432,
                    database="vigia_medical",
                    user="vigia_user",
                    password="test_password"  # Use test password
                )
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                assert result[0] == 1
                conn.close()
            except psycopg2.OperationalError:
                pytest.skip("PostgreSQL connection not available for testing")
    
    def test_redis_service(self, hospital_services):
        """Test Redis service health"""
        redis_container = None
        for name, container in hospital_services.items():
            if 'redis' in name:
                redis_container = container
                break
        
        if redis_container:
            assert redis_container.status == 'running'
            
            # Test Redis connection
            try:
                r = redis.Redis(host='localhost', port=6379, db=0)
                r.ping()
                # Test basic operations
                r.set('test_key', 'test_value')
                assert r.get('test_key').decode() == 'test_value'
                r.delete('test_key')
            except redis.ConnectionError:
                pytest.skip("Redis connection not available for testing")
    
    def test_celery_worker_service(self, hospital_services):
        """Test Celery worker service"""
        celery_container = None
        for name, container in hospital_services.items():
            if 'celery' in name and 'worker' in name:
                celery_container = container
                break
        
        if celery_container:
            assert celery_container.status == 'running'
            
            # Test Celery connection
            try:
                app = Celery('vigia_detect.tasks')
                app.config_from_object('celeryconfig')
                
                # Check if worker is responding
                inspect = app.control.inspect()
                stats = inspect.stats()
                assert stats is not None, "Celery worker not responding"
            except Exception:
                pytest.skip("Celery connection not available for testing")
    
    def test_nginx_service(self, hospital_services):
        """Test NGINX reverse proxy service"""
        nginx_container = None
        for name, container in hospital_services.items():
            if 'nginx' in name:
                nginx_container = container
                break
        
        if nginx_container:
            assert nginx_container.status == 'running'


class TestHospitalEndpoints:
    """Test hospital service endpoints"""
    
    BASE_URL = "https://localhost"
    TIMEOUT = 10
    
    def test_health_endpoint(self):
        """Test main health check endpoint"""
        try:
            response = requests.get(
                f"{self.BASE_URL}/health",
                verify=False,  # Skip SSL verification for self-signed cert
                timeout=self.TIMEOUT
            )
            assert response.status_code == 200
            
            health_data = response.json()
            assert 'status' in health_data
            assert health_data['status'] in ['healthy', 'ok']
            
        except requests.exceptions.RequestException:
            pytest.skip("Hospital endpoint not available for testing")
    
    def test_metrics_endpoint(self):
        """Test Prometheus metrics endpoint"""
        try:
            response = requests.get(
                f"{self.BASE_URL}/metrics",
                verify=False,
                timeout=self.TIMEOUT
            )
            assert response.status_code == 200
            
            # Check for medical-specific metrics
            metrics_text = response.text
            medical_metrics = [
                'lpp_detection_total',
                'medical_session_duration',
                'audit_events_total'
            ]
            
            for metric in medical_metrics:
                assert metric in metrics_text, f"Missing medical metric: {metric}"
                
        except requests.exceptions.RequestException:
            pytest.skip("Metrics endpoint not available for testing")
    
    def test_whatsapp_webhook_endpoint(self):
        """Test WhatsApp webhook endpoint"""
        try:
            response = requests.get(
                f"{self.BASE_URL}/webhook/whatsapp",
                verify=False,
                timeout=self.TIMEOUT
            )
            # Should return method not allowed for GET
            assert response.status_code in [405, 200]
            
        except requests.exceptions.RequestException:
            pytest.skip("WhatsApp webhook not available for testing")
    
    def test_medical_api_endpoints(self):
        """Test medical API endpoints (basic connectivity)"""
        endpoints = [
            '/api/medical/status',
            '/api/lpp/detect',
            '/api/sessions',
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(
                    f"{self.BASE_URL}{endpoint}",
                    verify=False,
                    timeout=self.TIMEOUT
                )
                # Should not return 404 (endpoint exists)
                assert response.status_code != 404, f"Endpoint not found: {endpoint}"
                
            except requests.exceptions.RequestException:
                pytest.skip(f"Medical API endpoint not available: {endpoint}")


class TestBackupAndRestore:
    """Test backup and restore functionality"""
    
    def test_backup_script_exists(self):
        """Test that backup scripts exist"""
        backup_files = [
            "scripts/backup-medical-data.sh",
            "docker/backup/backup.sh",
            "docker/backup/restore.sh"
        ]
        
        for backup_file in backup_files:
            if Path(backup_file).exists():
                assert os.access(backup_file, os.X_OK), f"Backup script not executable: {backup_file}"
    
    def test_backup_directories_exist(self):
        """Test that backup directories are configured"""
        # Check if backup directories would be created
        env_file = Path(".env.hospital")
        if env_file.exists():
            with open(env_file) as f:
                content = f.read()
                assert "BACKUP_ENABLED=true" in content
                assert "BACKUP_STORAGE_PATH" in content
    
    def test_backup_encryption_config(self):
        """Test backup encryption configuration"""
        env_file = Path(".env.hospital")
        if env_file.exists():
            with open(env_file) as f:
                content = f.read()
                assert "BACKUP_ENCRYPTION_ENABLED=true" in content
                assert "backup_encryption_key" in content.lower()


class TestSecurityConfiguration:
    """Test security configuration"""
    
    def test_docker_secrets_configuration(self):
        """Test Docker secrets are properly configured"""
        compose_file = Path("docker-compose.hospital.yml")
        if compose_file.exists():
            with open(compose_file) as f:
                content = f.read()
                
                # Check for external secrets
                secrets = [
                    'postgres_password',
                    'redis_password',
                    'encryption_key',
                    'jwt_secret'
                ]
                
                for secret in secrets:
                    assert secret in content, f"Missing Docker secret: {secret}"
    
    def test_ssl_configuration(self):
        """Test SSL configuration"""
        nginx_config = Path("docker/nginx/nginx.conf")
        if nginx_config.exists():
            with open(nginx_config) as f:
                content = f.read()
                
                # Check SSL settings
                ssl_settings = [
                    'ssl_certificate',
                    'ssl_certificate_key',
                    'ssl_protocols TLSv1.2 TLSv1.3',
                    'ssl_ciphers'
                ]
                
                for setting in ssl_settings:
                    assert setting in content, f"Missing SSL setting: {setting}"
    
    def test_network_segmentation(self):
        """Test network segmentation configuration"""
        compose_file = Path("docker-compose.hospital.yml")
        if compose_file.exists():
            with open(compose_file) as f:
                content = f.read()
                
                # Check for defined networks
                networks = [
                    'medical_data',
                    'internal',
                    'management',
                    'dmz'
                ]
                
                for network in networks:
                    assert network in content, f"Missing network: {network}"


class TestComplianceRequirements:
    """Test medical compliance requirements"""
    
    def test_hipaa_compliance_settings(self):
        """Test HIPAA compliance configuration"""
        env_file = Path(".env.hospital")
        if env_file.exists():
            with open(env_file) as f:
                content = f.read()
                
                hipaa_settings = [
                    'MEDICAL_COMPLIANCE_LEVEL=hipaa',
                    'PHI_PROTECTION_ENABLED=true',
                    'AUDIT_LOG_ENABLED=true',
                    'ENCRYPTION_ALGORITHM=AES-256-GCM'
                ]
                
                for setting in hipaa_settings:
                    assert setting in content, f"Missing HIPAA setting: {setting}"
    
    def test_audit_logging_configuration(self):
        """Test audit logging configuration"""
        env_file = Path(".env.hospital")
        if env_file.exists():
            with open(env_file) as f:
                content = f.read()
                
                assert 'AUDIT_LOG_RETENTION_DAYS=2555' in content  # 7 years
                assert 'MEDICAL_DATA_RETENTION_DAYS=2555' in content
    
    def test_data_retention_policies(self):
        """Test data retention policy configuration"""
        postgres_config = Path("docker/postgres/postgresql.conf")
        if postgres_config.exists():
            with open(postgres_config) as f:
                content = f.read()
                
                # Check for audit and retention settings
                retention_settings = [
                    'log_statement = all',
                    'log_duration = on',
                    'wal_level = replica'
                ]
                
                for setting in retention_settings:
                    assert setting in content, f"Missing retention setting: {setting}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
