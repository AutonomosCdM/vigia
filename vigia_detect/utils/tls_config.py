"""
TLS/SSL Configuration for Vigia Medical AI System
Production-grade TLS configuration with medical compliance
HIPAA-compliant secure communications
"""

import ssl
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TLSProfile(Enum):
    """TLS security profiles for different environments"""
    DEVELOPMENT = "development"      # Relaxed for dev
    MEDICAL_GRADE = "medical_grade"  # HIPAA/Medical compliance
    HIGH_SECURITY = "high_security"  # Maximum security
    GOVERNMENT = "government"        # Government/FIPS compliance


@dataclass
class TLSConfig:
    """TLS configuration settings"""
    profile: TLSProfile
    min_version: str
    ciphers: str
    cert_file: Optional[str] = None
    key_file: Optional[str] = None
    ca_file: Optional[str] = None
    verify_mode: str = "required"
    check_hostname: bool = True
    client_cert_required: bool = False
    
    
class VigiaSSLContext:
    """Medical-grade SSL context manager"""
    
    # HIPAA-compliant cipher suites (exclude weak ciphers)
    MEDICAL_CIPHERS = ":".join([
        "ECDHE+AESGCM",
        "ECDHE+CHACHA20",
        "DHE+AESGCM", 
        "DHE+CHACHA20",
        "!aNULL",
        "!MD5",
        "!DSS",
        "!RC4",
        "!3DES",
        "!DES",
        "!EXPORT",
        "!LOW",
        "!MEDIUM"
    ])
    
    # High security cipher suites
    HIGH_SECURITY_CIPHERS = ":".join([
        "ECDHE+AESGCM:256",
        "ECDHE+CHACHA20",
        "!aNULL",
        "!eNULL", 
        "!EXPORT",
        "!DES",
        "!RC4",
        "!MD5",
        "!PSK",
        "!SRP",
        "!CAMELLIA"
    ])
    
    # Development ciphers (more permissive)
    DEV_CIPHERS = ":".join([
        "ECDHE+AESGCM",
        "ECDHE+AES",
        "DHE+AESGCM",
        "DHE+AES",
        "!aNULL",
        "!MD5",
        "!RC4"
    ])
    
    def __init__(self, profile: TLSProfile = TLSProfile.MEDICAL_GRADE):
        """Initialize SSL context with specified profile"""
        self.profile = profile
        self.config = self._get_config_for_profile(profile)
        
    def _get_config_for_profile(self, profile: TLSProfile) -> TLSConfig:
        """Get TLS configuration for security profile"""
        configs = {
            TLSProfile.DEVELOPMENT: TLSConfig(
                profile=profile,
                min_version="TLSv1.2",
                ciphers=self.DEV_CIPHERS,
                verify_mode="none",
                check_hostname=False,
                client_cert_required=False
            ),
            TLSProfile.MEDICAL_GRADE: TLSConfig(
                profile=profile,
                min_version="TLSv1.3",
                ciphers=self.MEDICAL_CIPHERS,
                verify_mode="required",
                check_hostname=True,
                client_cert_required=False
            ),
            TLSProfile.HIGH_SECURITY: TLSConfig(
                profile=profile,
                min_version="TLSv1.3",
                ciphers=self.HIGH_SECURITY_CIPHERS,
                verify_mode="required",
                check_hostname=True,
                client_cert_required=True
            ),
            TLSProfile.GOVERNMENT: TLSConfig(
                profile=profile,
                min_version="TLSv1.3",
                ciphers=self.HIGH_SECURITY_CIPHERS,
                verify_mode="required",
                check_hostname=True,
                client_cert_required=True
            )
        }
        return configs[profile]
    
    def create_server_context(self, 
                            cert_file: Optional[str] = None,
                            key_file: Optional[str] = None,
                            ca_file: Optional[str] = None) -> ssl.SSLContext:
        """
        Create SSL context for server applications
        
        Args:
            cert_file: Server certificate file path
            key_file: Private key file path  
            ca_file: CA certificate file path
            
        Returns:
            Configured SSL context
        """
        # Create context with appropriate protocol
        if self.config.min_version == "TLSv1.3":
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.minimum_version = ssl.TLSVersion.TLSv1_3
        else:
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        # Configure cipher suites
        context.set_ciphers(self.config.ciphers)
        
        # Set verification mode
        verify_modes = {
            "none": ssl.CERT_NONE,
            "optional": ssl.CERT_OPTIONAL,
            "required": ssl.CERT_REQUIRED
        }
        context.verify_mode = verify_modes.get(self.config.verify_mode, ssl.CERT_REQUIRED)
        
        # Configure hostname checking
        context.check_hostname = self.config.check_hostname
        
        # Load certificates
        cert_file = cert_file or self.config.cert_file or self._find_cert_file()
        key_file = key_file or self.config.key_file or self._find_key_file()
        
        if cert_file and key_file:
            if Path(cert_file).exists() and Path(key_file).exists():
                context.load_cert_chain(cert_file, key_file)
                logger.info(f"Loaded server certificates: {cert_file}")
            else:
                logger.warning(f"Certificate files not found: {cert_file}, {key_file}")
        
        # Load CA certificates
        ca_file = ca_file or self.config.ca_file
        if ca_file and Path(ca_file).exists():
            context.load_verify_locations(ca_file)
            logger.info(f"Loaded CA certificates: {ca_file}")
        
        # Medical-grade security hardening
        if self.profile in [TLSProfile.MEDICAL_GRADE, TLSProfile.HIGH_SECURITY]:
            # Disable compression (CRIME attack prevention)
            context.options |= ssl.OP_NO_COMPRESSION
            
            # Disable SSLv2 and SSLv3
            context.options |= ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3
            
            # Prefer server cipher order
            context.options |= ssl.OP_CIPHER_SERVER_PREFERENCE
            
            # Disable session resumption (for maximum security)
            if self.profile == TLSProfile.HIGH_SECURITY:
                context.options |= ssl.OP_NO_TICKET
        
        # Client certificate requirement
        if self.config.client_cert_required:
            context.verify_mode = ssl.CERT_REQUIRED
        
        logger.info(f"Created SSL server context with {self.profile.value} profile")
        return context
    
    def create_client_context(self, 
                            ca_file: Optional[str] = None,
                            cert_file: Optional[str] = None,
                            key_file: Optional[str] = None) -> ssl.SSLContext:
        """
        Create SSL context for client connections
        
        Args:
            ca_file: CA certificate file path
            cert_file: Client certificate file path
            key_file: Client private key file path
            
        Returns:
            Configured SSL context
        """
        # Create default client context
        context = ssl.create_default_context()
        
        # Set minimum TLS version
        if self.config.min_version == "TLSv1.3":
            context.minimum_version = ssl.TLSVersion.TLSv1_3
        else:
            context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        # Configure cipher suites
        context.set_ciphers(self.config.ciphers)
        
        # Configure verification
        if self.config.verify_mode == "none":
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        else:
            context.check_hostname = self.config.check_hostname
            context.verify_mode = ssl.CERT_REQUIRED
        
        # Load CA certificates
        ca_file = ca_file or self.config.ca_file
        if ca_file and Path(ca_file).exists():
            context.load_verify_locations(ca_file)
        
        # Load client certificates (for mutual TLS)
        cert_file = cert_file or self.config.cert_file
        key_file = key_file or self.config.key_file
        
        if cert_file and key_file:
            if Path(cert_file).exists() and Path(key_file).exists():
                context.load_cert_chain(cert_file, key_file)
                logger.info(f"Loaded client certificates for mTLS")
        
        logger.info(f"Created SSL client context with {self.profile.value} profile")
        return context
    
    def _find_cert_file(self) -> Optional[str]:
        """Find server certificate file in standard locations"""
        cert_locations = [
            "/etc/ssl/certs/vigia.crt",
            "/etc/vigia/certs/server.crt",
            "./certs/server.crt",
            "./ssl/server.crt",
            os.getenv("SSL_CERT_FILE")
        ]
        
        for location in cert_locations:
            if location and Path(location).exists():
                return location
        
        return None
    
    def _find_key_file(self) -> Optional[str]:
        """Find private key file in standard locations"""
        key_locations = [
            "/etc/ssl/private/vigia.key",
            "/etc/vigia/certs/server.key", 
            "./certs/server.key",
            "./ssl/server.key",
            os.getenv("SSL_KEY_FILE")
        ]
        
        for location in key_locations:
            if location and Path(location).exists():
                return location
        
        return None
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate TLS configuration"""
        issues = []
        
        # Check minimum TLS version
        if self.config.min_version == "TLSv1.0":
            issues.append("TLS 1.0 is deprecated and insecure")
        elif self.config.min_version == "TLSv1.1":
            issues.append("TLS 1.1 is deprecated")
        
        # Check cipher suites
        if "RC4" in self.config.ciphers:
            issues.append("RC4 cipher is insecure")
        if "MD5" in self.config.ciphers:
            issues.append("MD5 is cryptographically broken")
        if "3DES" in self.config.ciphers:
            issues.append("3DES is deprecated")
        
        # Medical compliance checks
        if self.profile == TLSProfile.MEDICAL_GRADE:
            if self.config.min_version != "TLSv1.3":
                issues.append("Medical grade requires TLS 1.3")
            if not self.config.check_hostname:
                issues.append("Medical grade requires hostname verification")
        
        return {
            "profile": self.profile.value,
            "valid": len(issues) == 0,
            "issues": issues,
            "min_version": self.config.min_version,
            "ciphers_count": len(self.config.ciphers.split(":")),
            "cert_file_exists": bool(self._find_cert_file()),
            "key_file_exists": bool(self._find_key_file())
        }


def get_ssl_context(profile: Union[str, TLSProfile] = TLSProfile.MEDICAL_GRADE,
                   server: bool = True,
                   **kwargs) -> ssl.SSLContext:
    """
    Convenience function to get SSL context
    
    Args:
        profile: TLS security profile
        server: Whether this is for server (True) or client (False)
        **kwargs: Additional SSL configuration
        
    Returns:
        Configured SSL context
    """
    if isinstance(profile, str):
        profile = TLSProfile(profile)
    
    ssl_manager = VigiaSSLContext(profile)
    
    if server:
        return ssl_manager.create_server_context(**kwargs)
    else:
        return ssl_manager.create_client_context(**kwargs)


def create_self_signed_cert(cert_file: str, key_file: str, 
                          hostname: str = "localhost",
                          org: str = "Vigia Medical AI") -> bool:
    """
    Create self-signed certificate for development
    
    Args:
        cert_file: Certificate output file
        key_file: Private key output file
        hostname: Server hostname
        org: Organization name
        
    Returns:
        True if successful
    """
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from datetime import datetime, timedelta
        import ipaddress
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CL"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Santiago"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Santiago"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, org),
            x509.NameAttribute(NameOID.COMMON_NAME, hostname),
        ])
        
        # Build certificate
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(hostname),
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Write certificate
        Path(cert_file).parent.mkdir(parents=True, exist_ok=True)
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        # Write private key
        with open(key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Set secure permissions
        os.chmod(cert_file, 0o644)
        os.chmod(key_file, 0o600)
        
        logger.info(f"Created self-signed certificate: {cert_file}")
        return True
        
    except ImportError:
        logger.error("cryptography library required for certificate generation")
        return False
    except Exception as e:
        logger.error(f"Failed to create self-signed certificate: {e}")
        return False