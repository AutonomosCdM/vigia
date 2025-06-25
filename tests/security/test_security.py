"""
Security test suite for Vigia v1.0.0-rc1
Tests for common vulnerabilities and security issues
"""

import pytest
import os
import re
import tempfile
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from vigia_detect.utils.security_validator import (
    SecurityValidator, 
    validate_and_sanitize_image,
    sanitize_user_input
)


class TestInputValidation:
    """Test input validation and sanitization"""
    
    def setup_method(self):
        """Setup for each test"""
        self.validator = SecurityValidator()
    
    def test_sql_injection_prevention(self):
        """Test SQL injection pattern detection"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "1; DELETE FROM products",
            "' UNION SELECT * FROM passwords--"
        ]
        
        for malicious in malicious_inputs:
            sanitized = self.validator.sanitize_text(malicious)
            assert "DROP" not in sanitized
            assert "DELETE" not in sanitized
            assert "UNION" not in sanitized
            assert "--" not in sanitized
    
    def test_xss_prevention(self):
        """Test XSS attack prevention"""
        xss_attempts = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<body onload=alert('XSS')>",
            "';alert(String.fromCharCode(88,83,83))//",
        ]
        
        for xss in xss_attempts:
            sanitized = self.validator.sanitize_text(xss)
            assert "<script" not in sanitized
            assert "javascript:" not in sanitized
            assert "onerror" not in sanitized
            assert "onload" not in sanitized
            # Check HTML entities are escaped
            assert "&lt;" in sanitized or "<" not in sanitized
            assert "&gt;" in sanitized or ">" not in sanitized
    
    def test_path_traversal_prevention(self):
        """Test path traversal attack prevention"""
        path_attacks = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "%2e%2e%2f%2e%2e%2f",
            "....//....//etc/passwd",
        ]
        
        for path in path_attacks:
            assert self.validator._contains_path_traversal(path)
            sanitized = self.validator.sanitize_filename(path)
            assert ".." not in sanitized
            assert "/" not in sanitized
            assert "\\" not in sanitized
    
    def test_filename_sanitization(self):
        """Test filename sanitization"""
        dangerous_filenames = [
            "../../evil.jpg",
            "file\x00.jpg",  # Null byte
            "very" * 100 + ".jpg",  # Too long
            "file<script>.jpg",
            "file|pipe.jpg",
        ]
        
        for filename in dangerous_filenames:
            sanitized = self.validator.sanitize_filename(filename)
            assert len(sanitized) <= 255
            assert "\x00" not in sanitized
            assert ".." not in sanitized
            assert "<" not in sanitized
            assert "|" not in sanitized
    
    def test_patient_code_validation(self):
        """Test patient code validation"""
        # Valid codes
        valid_codes = ["CD-2025-001", "AB-2024-999", "ZZ-2023-000"]
        for code in valid_codes:
            is_valid, error = self.validator.validate_patient_code(code)
            assert is_valid, f"Valid code {code} rejected: {error}"
        
        # Invalid codes
        invalid_codes = [
            "CD2025001",  # Missing hyphens
            "cd-2025-001",  # Lowercase
            "CD-2025-1",  # Wrong digit count
            "'; DROP TABLE--",  # SQL injection
            "",  # Empty
            None,  # None
        ]
        
        for code in invalid_codes:
            if code is not None:
                is_valid, error = self.validator.validate_patient_code(code)
                assert not is_valid, f"Invalid code {code} accepted"


class TestImageSecurity:
    """Test image upload security"""
    
    def setup_method(self):
        """Setup for each test"""
        self.validator = SecurityValidator()
        self.test_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup after each test"""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_image_size_limit(self):
        """Test image size validation"""
        # Create a file that's too large (simulate)
        large_file = Path(self.test_dir) / "large.jpg"
        with open(large_file, 'wb') as f:
            f.write(b'0' * (51 * 1024 * 1024))  # 51MB
        
        is_valid, error = self.validator.validate_image(str(large_file))
        assert not is_valid
        assert "too large" in error.lower()
    
    def test_invalid_file_types(self):
        """Test rejection of non-image files"""
        # Create files with wrong extensions
        invalid_files = [
            "test.exe",
            "test.sh",
            "test.php",
            "test.js",
        ]
        
        for filename in invalid_files:
            file_path = Path(self.test_dir) / filename
            file_path.write_text("malicious content")
            
            is_valid, error = self.validator.validate_image(str(file_path))
            assert not is_valid
            assert "Invalid extension" in error or "Invalid MIME" in error
    
    def test_file_extension_spoofing(self):
        """Test detection of spoofed file extensions"""
        # Create a text file with image extension
        spoofed_file = Path(self.test_dir) / "fake.jpg"
        spoofed_file.write_text("This is not an image")
        
        is_valid, error = self.validator.validate_image(str(spoofed_file))
        assert not is_valid


class TestWebhookSecurity:
    """Test webhook URL validation"""
    
    def setup_method(self):
        """Setup for each test"""
        self.validator = SecurityValidator()
    
    def test_ssrf_prevention(self):
        """Test Server-Side Request Forgery prevention"""
        dangerous_urls = [
            "http://localhost/admin",
            "http://127.0.0.1:8080",
            "http://169.254.169.254/latest/meta-data/",  # AWS metadata
            "http://[::1]/",  # IPv6 localhost
            "http://0.0.0.0:8000",
            "http://192.168.1.1/",  # Private IP
            "http://10.0.0.1/",  # Private IP
            "http://172.16.0.1/",  # Private IP
        ]
        
        for url in dangerous_urls:
            is_valid, error = self.validator.validate_webhook_url(url)
            assert not is_valid, f"Dangerous URL {url} was accepted"
            assert error is not None, f"No error message for {url}"
            # Check for either "not allowed" or "invalid" in error
            assert any(msg in error.lower() for msg in ["not allowed", "invalid"]), \
                f"Unexpected error message for {url}: {error}"
    
    def test_valid_webhook_urls(self):
        """Test acceptance of valid webhook URLs"""
        valid_urls = [
            "https://api.example.com/webhook",
            "https://webhook.site/unique-id",
            "http://public-api.com/webhook",
            "https://app.company.io/api/v1/webhook",
        ]
        
        for url in valid_urls:
            is_valid, error = self.validator.validate_webhook_url(url)
            assert is_valid, f"Valid URL {url} rejected: {error}"


class TestDataMasking:
    """Test sensitive data masking"""
    
    def setup_method(self):
        """Setup for each test"""
        self.validator = SecurityValidator()
    
    def test_api_key_masking(self):
        """Test API key masking for logs"""
        api_key = "sk_test_1234567890abcdefghijklmnop"
        masked = self.validator.mask_sensitive_data(api_key)
        
        assert "sk_t" in masked  # Start visible
        assert "mnop" in masked  # End visible
        assert "*" * 20 in masked  # Middle masked
        assert api_key not in masked  # Original not visible
    
    def test_token_hashing(self):
        """Test token hashing for logs"""
        token = "secret_token_12345"
        hashed1 = self.validator.hash_sensitive_data(token)
        hashed2 = self.validator.hash_sensitive_data(token)
        
        assert hashed1 == hashed2  # Consistent hashing
        assert len(hashed1) == 16  # Truncated hash
        assert token not in hashed1  # Original not visible


class TestEndpointSecurity:
    """Test API endpoint security"""
    


class TestDockerSecurity:
    """Test Docker container security"""
    
    def test_dockerfile_security(self):
        """Test Dockerfile follows security best practices"""
        dockerfile_path = Path("Dockerfile")
        if dockerfile_path.exists():
            content = dockerfile_path.read_text()
            
            # Check for non-root user
            assert "USER" in content, "Dockerfile should specify non-root user"
            assert "vigia" in content, "Should use 'vigia' user"
            
            # Check for security options
            assert "python:3.11-slim" in content, "Should use slim base image"
            
            # Check no sudo installed
            assert "sudo" not in content.lower(), "Should not install sudo"
    
    def test_docker_compose_security(self):
        """Test docker-compose.yml security settings"""
        compose_path = Path("docker-compose.yml")
        if compose_path.exists():
            content = compose_path.read_text()
            
            # Check security options
            assert "no-new-privileges:true" in content
            assert "cap_drop:" in content
            assert "ALL" in content
            assert "read_only: true" in content


# Run basic security checks
def test_no_hardcoded_secrets():
    """Ensure no hardcoded secrets in codebase"""
    # This is a simplified version - in production use git-secrets or similar
    patterns_to_check = [
        (r'api_key\s*=\s*["\'][A-Za-z0-9]{20,}["\']', "Hardcoded API key"),
        (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
        (r'secret\s*=\s*["\'][A-Za-z0-9]{20,}["\']', "Hardcoded secret"),
    ]
    
    issues = []
    for py_file in Path("vigia_detect").rglob("*.py"):
        # Skip test files
        if "test" in str(py_file):
            continue
            
        content = py_file.read_text()
        for pattern, desc in patterns_to_check:
            if re.search(pattern, content) and "os.environ" not in content:
                issues.append(f"{py_file}: {desc}")
    
    assert len(issues) == 0, f"Found hardcoded secrets: {issues}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])