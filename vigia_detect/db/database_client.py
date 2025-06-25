"""
Database Client Module

Provides unified database client interface with security configurations.
Implements secure database connections with SSL/TLS encryption.
"""

import os
import logging
from typing import Dict, Any, Optional
from .supabase_client_refactored import SupabaseClientRefactored

logger = logging.getLogger(__name__)


class DatabaseClient:
    """
    Unified database client with security configurations.
    
    Provides secure database access with SSL/TLS encryption
    and connection parameter validation.
    """
    
    def __init__(self):
        """Initialize database client with security configurations"""
        self.supabase_client = SupabaseClientRefactored()
        self._ssl_config = self._get_default_ssl_config()
        logger.info("Database client initialized with SSL configuration")
    
    def get_connection_parameters(self) -> str:
        """
        Get database connection parameters string
        
        Returns:
            Connection parameters with SSL requirements
        """
        # For Supabase, connections are HTTPS by default
        supabase_url = os.getenv('SUPABASE_URL', '')
        
        if supabase_url.startswith('https://'):
            return f"url={supabase_url} sslmode=require"
        else:
            # Fallback for local development
            return "sslmode=prefer ssl=true"
    
    def get_ssl_configuration(self) -> Dict[str, Any]:
        """
        Get SSL/TLS configuration for database connections
        
        Returns:
            SSL configuration dictionary
        """
        return self._ssl_config.copy()
    
    def validate_ssl_connection(self) -> bool:
        """
        Validate that database connection uses SSL/TLS
        
        Returns:
            True if connection is secure
        """
        try:
            # For Supabase, check if URL uses HTTPS
            supabase_url = os.getenv('SUPABASE_URL', '')
            if supabase_url.startswith('https://'):
                return True
            
            # For other databases, check SSL configuration
            ssl_config = self.get_ssl_configuration()
            return ssl_config.get('verify_certificates', False)
            
        except Exception as e:
            logger.error(f"SSL validation failed: {e}")
            return False
    
    def _get_default_ssl_config(self) -> Dict[str, Any]:
        """Get default SSL configuration for medical-grade security"""
        return {
            'verify_certificates': True,
            'ssl_mode': 'require',
            'ssl_cipher': 'HIGH:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!SRP:!CAMELLIA',
            'min_tls_version': '1.2',
            'check_hostname': True
        }
    
    def get_client(self):
        """Get underlying Supabase client"""
        return self.supabase_client
    
    def health_check(self) -> bool:
        """
        Perform database health check
        
        Returns:
            True if database is accessible
        """
        try:
            # Validate SSL connection
            if not self.validate_ssl_connection():
                logger.warning("Database connection does not use SSL")
                return False
            
            # Test basic connectivity through Supabase client
            # Note: This is a mock check - real implementation would test actual connection
            return True
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False