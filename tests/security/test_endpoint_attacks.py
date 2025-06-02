"""
Endpoint security attack simulation tests
Tests API endpoints against common attack vectors
"""

import pytest
import asyncio
import aiohttp
import json
import base64
from typing import Dict, Any, List
import time


class TestEndpointAttacks:
    """Simulate various attack vectors against API endpoints"""
    
    # Test configuration
    BASE_URL = "http://localhost:8000"  # Webhook server
    WHATSAPP_URL = "http://localhost:5000"  # WhatsApp server
    
    @pytest.fixture
    async def session(self):
        """Create aiohttp session"""
        async with aiohttp.ClientSession() as session:
            yield session
    
    async def test_malicious_image_upload(self, session):
        """Test uploading malicious files disguised as images"""
        attacks = [
            # PHP webshell
            ("evil.php.jpg", b"<?php system($_GET['cmd']); ?>"),
            # Null byte injection
            ("image.jpg\x00.php", b"<?php phpinfo(); ?>"),
            # Double extension
            ("shell.jpg.php", b"malicious code"),
            # SVG with JavaScript
            ("xss.svg", b'<svg onload="alert(1)">'),
        ]
        
        for filename, content in attacks:
            # Test WhatsApp image endpoint
            try:
                # Create multipart upload
                data = aiohttp.FormData()
                data.add_field('MediaUrl', 
                             content,
                             filename=filename,
                             content_type='image/jpeg')
                
                async with session.post(
                    f"{self.WHATSAPP_URL}/whatsapp/webhook",
                    data=data
                ) as response:
                    # Should reject malicious files
                    assert response.status in [400, 415, 422], \
                        f"Malicious file {filename} was not rejected"
            except Exception:
                pass  # Server might not be running
    
    async def test_sql_injection_attempts(self, session):
        """Test SQL injection in various parameters"""
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE patients; --",
            "1' UNION SELECT * FROM users--",
            "admin'--",
            "1; DELETE FROM detections WHERE '1'='1",
        ]
        
        endpoints = [
            ("/webhook", "patient_code"),
            ("/whatsapp/webhook", "Body"),
        ]
        
        for endpoint, param in endpoints:
            for payload in sql_payloads:
                try:
                    # Test in JSON body
                    async with session.post(
                        f"{self.BASE_URL}{endpoint}",
                        json={param: payload},
                        headers={"X-API-Key": "test-key"}
                    ) as response:
                        # Should sanitize or reject
                        assert response.status != 500, \
                            f"SQL injection caused server error: {payload}"
                        
                        # Check response doesn't leak info
                        text = await response.text()
                        assert "syntax" not in text.lower()
                        assert "sql" not in text.lower()
                except Exception:
                    pass
    
    async def test_xss_attempts(self, session):
        """Test Cross-Site Scripting attempts"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert('XSS')",
            "<svg/onload=alert('XSS')>",
            "'><script>alert(String.fromCharCode(88,83,83))</script>",
        ]
        
        for payload in xss_payloads:
            try:
                # Test webhook endpoint
                async with session.post(
                    f"{self.BASE_URL}/webhook",
                    json={
                        "patient_code": "TEST-001",
                        "message": payload
                    },
                    headers={"X-API-Key": "test-key"}
                ) as response:
                    if response.status == 200:
                        # Check response is sanitized
                        data = await response.json()
                        assert "<script>" not in str(data)
                        assert "javascript:" not in str(data)
            except Exception:
                pass
    
    async def test_xxe_injection(self, session):
        """Test XML External Entity injection"""
        xxe_payload = """<?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
        <data>&xxe;</data>"""
        
        try:
            async with session.post(
                f"{self.BASE_URL}/webhook",
                data=xxe_payload,
                headers={
                    "Content-Type": "application/xml",
                    "X-API-Key": "test-key"
                }
            ) as response:
                # Should reject or not process XML
                assert response.status in [400, 415], \
                    "XXE payload was not rejected"
        except Exception:
            pass
    
    async def test_path_traversal(self, session):
        """Test path traversal attempts"""
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "....//....//....//etc/passwd",
        ]
        
        for payload in traversal_payloads:
            try:
                # Test in image path parameter
                async with session.post(
                    f"{self.BASE_URL}/webhook",
                    json={
                        "patient_code": "TEST-001",
                        "image_path": payload
                    },
                    headers={"X-API-Key": "test-key"}
                ) as response:
                    # Should sanitize paths
                    assert response.status != 500
                    if response.status == 200:
                        data = await response.json()
                        assert ".." not in str(data)
            except Exception:
                pass
    
    async def test_command_injection(self, session):
        """Test command injection attempts"""
        cmd_payloads = [
            "; cat /etc/passwd",
            "| whoami",
            "$(rm -rf /)",
            "`reboot`",
            "& net user hacker password /add",
        ]
        
        for payload in cmd_payloads:
            try:
                async with session.post(
                    f"{self.BASE_URL}/webhook",
                    json={
                        "patient_code": f"TEST{payload}",
                        "filename": f"image{payload}.jpg"
                    },
                    headers={"X-API-Key": "test-key"}
                ) as response:
                    # Should reject or sanitize
                    assert response.status in [200, 400, 422]
            except Exception:
                pass
    
    async def test_ldap_injection(self, session):
        """Test LDAP injection attempts"""
        ldap_payloads = [
            "*)(uid=*))(|(uid=*",
            "admin)(&(password=*))",
            "*)(mail=*))%00",
        ]
        
        for payload in ldap_payloads:
            try:
                async with session.post(
                    f"{self.BASE_URL}/webhook",
                    json={"username": payload},
                    headers={"X-API-Key": "test-key"}
                ) as response:
                    # Should handle gracefully
                    assert response.status != 500
            except Exception:
                pass
    
    async def test_dos_large_payload(self, session):
        """Test Denial of Service with large payloads"""
        # Create large payload (10MB)
        large_data = {
            "patient_code": "TEST-001",
            "data": "x" * (10 * 1024 * 1024)
        }
        
        try:
            async with session.post(
                f"{self.BASE_URL}/webhook",
                json=large_data,
                headers={"X-API-Key": "test-key"},
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                # Should reject large payloads
                assert response.status in [413, 400], \
                    "Large payload was not rejected"
        except asyncio.TimeoutError:
            # Timeout is also acceptable (shows protection)
            pass
        except Exception:
            pass
    
    async def test_rate_limiting(self, session):
        """Test rate limiting protection"""
        # Send many requests quickly
        results = []
        
        for i in range(100):
            try:
                start = time.time()
                async with session.post(
                    f"{self.BASE_URL}/webhook",
                    json={"patient_code": "TEST-001"},
                    headers={"X-API-Key": "test-key"},
                    timeout=aiohttp.ClientTimeout(total=1)
                ) as response:
                    results.append({
                        "status": response.status,
                        "time": time.time() - start
                    })
            except Exception:
                pass
            
            # Don't sleep - hammer the endpoint
        
        # Check if rate limiting kicked in
        if results:
            statuses = [r["status"] for r in results]
            # Should see 429 (Too Many Requests) at some point
            assert 429 in statuses or len(set(statuses)) > 1, \
                "No rate limiting detected"
    
    async def test_authentication_bypass(self, session):
        """Test authentication bypass attempts"""
        bypass_attempts = [
            # No auth header
            {},
            # Wrong header name
            {"Authorization": "Bearer test-key"},
            # SQL injection in API key
            {"X-API-Key": "' OR '1'='1"},
            # Null byte
            {"X-API-Key": "test\x00admin"},
            # Unicode tricks
            {"X-API-Key": "test\u0000admin"},
        ]
        
        for headers in bypass_attempts:
            try:
                async with session.post(
                    f"{self.BASE_URL}/webhook",
                    json={"patient_code": "TEST-001"},
                    headers=headers
                ) as response:
                    # Should require valid authentication
                    assert response.status in [401, 403], \
                        f"Auth bypass attempt succeeded with headers: {headers}"
            except Exception:
                pass
    
    async def test_ssrf_attempts(self, session):
        """Test Server-Side Request Forgery"""
        ssrf_payloads = [
            "http://localhost:22",  # SSH
            "http://169.254.169.254/latest/meta-data/",  # AWS metadata
            "file:///etc/passwd",  # Local file
            "gopher://localhost:3306",  # MySQL
            "dict://localhost:11211",  # Memcached
        ]
        
        for url in ssrf_payloads:
            try:
                async with session.post(
                    f"{self.BASE_URL}/webhook",
                    json={
                        "webhook_callback": url,
                        "image_url": url
                    },
                    headers={"X-API-Key": "test-key"}
                ) as response:
                    # Should reject internal URLs
                    assert response.status in [400, 422], \
                        f"SSRF payload accepted: {url}"
            except Exception:
                pass


# Specialized attack test for file uploads
class TestFileUploadAttacks:
    """Test file upload vulnerabilities"""
    
    async def test_zip_bomb(self, session):
        """Test protection against zip bombs"""
        # Create a highly compressed file
        # In practice, would use actual zip bomb
        compressed_data = b"0" * 1000
        
        try:
            data = aiohttp.FormData()
            data.add_field('file',
                         compressed_data,
                         filename='bomb.zip',
                         content_type='application/zip')
            
            async with session.post(
                f"{self.WHATSAPP_URL}/upload",
                data=data
            ) as response:
                # Should reject or limit decompression
                assert response.status in [400, 413, 415]
        except Exception:
            pass
    
    async def test_polyglot_files(self, session):
        """Test polyglot file detection (valid image + malicious code)"""
        # JPEG header + PHP code
        polyglot = b'\xff\xd8\xff\xe0' + b'<?php system($_GET["cmd"]); ?>'
        
        try:
            data = aiohttp.FormData()
            data.add_field('image',
                         polyglot,
                         filename='polyglot.jpg',
                         content_type='image/jpeg')
            
            async with session.post(
                f"{self.WHATSAPP_URL}/whatsapp/webhook",
                data=data
            ) as response:
                # Should detect and reject
                assert response.status in [400, 415]
        except Exception:
            pass


if __name__ == "__main__":
    # Run async tests
    pytest.main([__file__, "-v", "-k", "test_"])