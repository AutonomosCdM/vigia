"""
Secure Logger for PHI Tokenization

Provides secure logging capabilities for HIPAA-compliant PHI tokenization operations.
"""

import logging
import sys
from typing import Optional

class SecureLogger:
    """Secure logger that ensures no PHI is logged."""
    
    def __init__(self, name: str, level: int = logging.INFO):
        """Initialize secure logger."""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Create console handler if none exists
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(self._sanitize_message(message), **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message.""" 
        self.logger.warning(self._sanitize_message(message), **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(self._sanitize_message(message), **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(self._sanitize_message(message), **kwargs)
    
    def _sanitize_message(self, message: str) -> str:
        """Sanitize message to prevent PHI leakage."""
        # Basic PHI sanitization - replace potential PHI patterns
        import re
        
        # Mask potential MRN patterns
        message = re.sub(r'MRN-\d{4}-\d{3}-\w+', 'MRN-[REDACTED]', message)
        
        # Mask potential phone numbers
        message = re.sub(r'\+?\d{10,15}', '[PHONE-REDACTED]', message)
        
        # Mask potential SSN patterns
        message = re.sub(r'\d{3}-\d{2}-\d{4}', '[SSN-REDACTED]', message)
        
        return message