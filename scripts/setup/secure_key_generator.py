#!/usr/bin/env python3
"""
Secure Key Generator for Vigia Medical AI System
Generates cryptographically secure keys for production deployment
HIPAA-compliant key generation with proper entropy
"""

import os
import secrets
import string
import base64
import hashlib
from pathlib import Path
from typing import Dict, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SecureKeyGenerator:
    """Production-grade secure key generator for medical systems"""
    
    def __init__(self):
        """Initialize with medical-grade security parameters"""
        self.min_key_length = 32  # 256 bits minimum
        self.recommended_length = 64  # 512 bits recommended
        
    def generate_secret_key(self, length: int = None) -> str:
        """
        Generate cryptographically secure secret key
        
        Args:
            length: Key length in bytes (default: 64 for 512-bit)
            
        Returns:
            Hex-encoded secure key
        """
        if length is None:
            length = self.recommended_length
            
        if length < self.min_key_length:
            raise ValueError(f"Key length must be at least {self.min_key_length} bytes")
            
        # Use secrets module for cryptographically secure random generation
        return secrets.token_hex(length)
    
    def generate_jwt_secret(self, length: int = None) -> str:
        """
        Generate JWT secret key with medical-grade security
        
        Args:
            length: Key length in bytes (default: 64)
            
        Returns:
            Base64-encoded JWT secret
        """
        if length is None:
            length = self.recommended_length
            
        key_bytes = secrets.token_bytes(length)
        return base64.b64encode(key_bytes).decode('utf-8')
    
    def generate_fernet_key(self) -> str:
        """
        Generate Fernet encryption key for PHI data
        
        Returns:
            Fernet-compatible encryption key
        """
        return Fernet.generate_key().decode('utf-8')
    
    def generate_api_key(self, prefix: str = "vigia", length: int = 32) -> str:
        """
        Generate API key with prefix for identification
        
        Args:
            prefix: Key prefix for identification
            length: Random part length in bytes
            
        Returns:
            Prefixed API key
        """
        random_part = secrets.token_urlsafe(length)
        return f"{prefix}_{random_part}"
    
    def generate_webhook_secret(self, length: int = 32) -> str:
        """
        Generate webhook verification secret
        
        Args:
            length: Secret length in bytes
            
        Returns:
            URL-safe webhook secret
        """
        return secrets.token_urlsafe(length)
    
    def generate_database_password(self, length: int = 32) -> str:
        """
        Generate secure database password
        
        Args:
            length: Password length
            
        Returns:
            Secure database password with mixed characters
        """
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        # Ensure we have at least one of each character type
        password = [
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.digits),
            secrets.choice("!@#$%^&*")
        ]
        
        # Fill the rest randomly
        for _ in range(length - 4):
            password.append(secrets.choice(alphabet))
        
        # Shuffle to avoid predictable pattern
        secrets.SystemRandom().shuffle(password)
        return ''.join(password)
    
    def generate_salt(self, length: int = 32) -> str:
        """
        Generate cryptographic salt
        
        Args:
            length: Salt length in bytes
            
        Returns:
            Hex-encoded salt
        """
        return secrets.token_hex(length)
    
    def derive_key_from_password(self, password: str, salt: bytes = None) -> Tuple[str, str]:
        """
        Derive encryption key from password using PBKDF2
        
        Args:
            password: Master password
            salt: Optional salt (generated if not provided)
            
        Returns:
            Tuple of (derived_key, salt_hex)
        """
        if salt is None:
            salt = os.urandom(32)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,  # NIST recommended minimum
        )
        
        derived_key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return derived_key.decode(), salt.hex()
    
    def generate_complete_env_keys(self) -> Dict[str, str]:
        """
        Generate complete set of environment keys for production
        
        Returns:
            Dictionary with all required environment variables
        """
        return {
            # Core application secrets
            'VIGIA_A2A_SECRET_KEY': self.generate_secret_key(64),
            'JWT_SECRET_KEY': self.generate_jwt_secret(64),
            'ENCRYPTION_KEY': self.generate_fernet_key(),
            
            # Database credentials
            'POSTGRES_PASSWORD': self.generate_database_password(32),
            'REDIS_PASSWORD': self.generate_database_password(24),
            
            # API keys
            'VIGIA_API_KEY': self.generate_api_key('vigia_api', 32),
            'WEBHOOK_SECRET': self.generate_webhook_secret(32),
            
            # Medical compliance keys
            'PHI_ENCRYPTION_KEY': self.generate_fernet_key(),
            'AUDIT_SIGNING_KEY': self.generate_secret_key(64),
            'MEDICAL_PROTOCOL_KEY': self.generate_secret_key(32),
            
            # Session and CSRF protection
            'SESSION_SECRET_KEY': self.generate_secret_key(32),
            'CSRF_SECRET_KEY': self.generate_secret_key(32),
            
            # MCP service keys
            'MCP_GATEWAY_KEY': self.generate_api_key('mcp', 32),
            'MCP_MEDICAL_KEY': self.generate_api_key('mcp_med', 32),
            
            # Communication secrets
            'SLACK_SIGNING_SECRET': self.generate_webhook_secret(32),
            'WHATSAPP_WEBHOOK_SECRET': self.generate_webhook_secret(32),
        }
    
    def validate_key_strength(self, key: str, min_entropy: float = 4.0) -> Tuple[bool, float]:
        """
        Validate key strength using entropy calculation
        
        Args:
            key: Key to validate
            min_entropy: Minimum required entropy per character
            
        Returns:
            Tuple of (is_strong, entropy_per_char)
        """
        if not key:
            return False, 0.0
        
        # Calculate character frequency
        char_counts = {}
        for char in key:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        # Calculate entropy
        key_length = len(key)
        entropy = 0.0
        for count in char_counts.values():
            probability = count / key_length
            if probability > 0:
                entropy -= probability * (probability.bit_length() - 1)
        
        entropy_per_char = entropy / key_length if key_length > 0 else 0.0
        return entropy_per_char >= min_entropy, entropy_per_char


def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate secure keys for Vigia Medical AI System"
    )
    parser.add_argument(
        '--type', 
        choices=['secret', 'jwt', 'fernet', 'api', 'webhook', 'database', 'all'],
        default='all',
        help='Type of key to generate'
    )
    parser.add_argument(
        '--length', 
        type=int, 
        help='Key length in bytes (where applicable)'
    )
    parser.add_argument(
        '--output', 
        type=str, 
        help='Output file for keys (default: stdout)'
    )
    parser.add_argument(
        '--env-format', 
        action='store_true',
        help='Output in .env file format'
    )
    
    args = parser.parse_args()
    generator = SecureKeyGenerator()
    
    if args.type == 'all':
        keys = generator.generate_complete_env_keys()
        
        if args.env_format:
            output = "\n".join([f"{k}={v}" for k, v in keys.items()])
        else:
            output = "\n".join([f"{k}: {v}" for k, v in keys.items()])
    else:
        # Generate single key
        if args.type == 'secret':
            key = generator.generate_secret_key(args.length)
        elif args.type == 'jwt':
            key = generator.generate_jwt_secret(args.length)
        elif args.type == 'fernet':
            key = generator.generate_fernet_key()
        elif args.type == 'api':
            key = generator.generate_api_key('vigia', args.length or 32)
        elif args.type == 'webhook':
            key = generator.generate_webhook_secret(args.length or 32)
        elif args.type == 'database':
            key = generator.generate_database_password(args.length or 32)
        
        output = key
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Keys written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()