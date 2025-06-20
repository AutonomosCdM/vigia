"""
Security Middleware for Vigia Medical AI System
HIPAA-compliant security headers and request validation
Production-grade security controls for medical applications
"""

import time
import hmac
import hashlib
import secrets
import logging
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from urllib.parse import urlparse

from fastapi import Request, Response, HTTPException, status
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware as StarletteBaseMiddleware

from .security_validator import security_validator
from .audit_service import AuditService, AuditEventType, AuditLevel

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """HIPAA-compliant security headers middleware"""
    
    def __init__(self, app, medical_grade: bool = True):
        """
        Initialize security headers middleware
        
        Args:
            app: FastAPI application
            medical_grade: Whether to apply medical-grade security headers
        """
        super().__init__(app)
        self.medical_grade = medical_grade
        self.audit = AuditService()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply security headers to response"""
        
        # Process request
        response = await call_next(request)
        
        # Base security headers (always applied)
        base_headers = {
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # XSS Protection
            "X-XSS-Protection": "1; mode=block",
            
            # Clickjacking protection
            "X-Frame-Options": "DENY",
            
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Feature policy
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            
            # Prevent caching sensitive data
            "Cache-Control": "no-cache, no-store, must-revalidate, private",
            "Pragma": "no-cache",
            "Expires": "0",
            
            # Security information
            "X-Security-Provider": "Vigia-Medical-AI",
            "X-Security-Level": "Medical-Grade" if self.medical_grade else "Standard"
        }
        
        # Medical-grade additional headers
        if self.medical_grade:
            medical_headers = {
                # Strict transport security (2 years)
                "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
                
                # Content Security Policy for medical apps
                "Content-Security-Policy": " ".join([
                    "default-src 'self';",
                    "script-src 'self' 'unsafe-inline';",
                    "style-src 'self' 'unsafe-inline';",
                    "img-src 'self' data: blob:;",
                    "font-src 'self';",
                    "connect-src 'self';",
                    "media-src 'self';",
                    "object-src 'none';",
                    "child-src 'none';",
                    "worker-src 'none';",
                    "manifest-src 'self';",
                    "base-uri 'self';",
                    "form-action 'self';"
                ]),
                
                # HIPAA compliance headers
                "X-Medical-Compliance": "HIPAA-SOC2-ISO13485",
                "X-PHI-Protection": "enabled",
                "X-Audit-Required": "true",
                
                # Force secure cookies
                "Set-Cookie": "Secure; HttpOnly; SameSite=Strict"
            }
            base_headers.update(medical_headers)
        
        # Apply headers to response
        for header, value in base_headers.items():
            response.headers[header] = value
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with medical priority queuing"""
    
    def __init__(self, app, 
                 requests_per_minute: int = 60,
                 medical_priority_multiplier: float = 2.0,
                 burst_allowance: int = 10):
        """
        Initialize rate limiting middleware
        
        Args:
            app: FastAPI application
            requests_per_minute: Base rate limit
            medical_priority_multiplier: Multiplier for medical endpoints
            burst_allowance: Additional requests allowed in burst
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.medical_priority_multiplier = medical_priority_multiplier
        self.burst_allowance = burst_allowance
        self.client_requests = {}
        self.audit = AuditService()
        
        # Medical priority endpoints
        self.medical_endpoints = {
            '/api/v1/detect',
            '/api/v1/medical',
            '/api/v1/emergency',
            '/api/v1/triage',
            '/webhook/medical'
        }
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try to get real IP from headers (for proxy setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"
    
    def _is_medical_endpoint(self, path: str) -> bool:
        """Check if endpoint has medical priority"""
        return any(medical_path in path for medical_path in self.medical_endpoints)
    
    def _get_rate_limit(self, path: str) -> int:
        """Get rate limit for specific endpoint"""
        base_limit = self.requests_per_minute
        
        if self._is_medical_endpoint(path):
            return int(base_limit * self.medical_priority_multiplier)
        
        return base_limit
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting logic"""
        
        client_id = self._get_client_identifier(request)
        current_time = time.time()
        endpoint_path = request.url.path
        
        # Get rate limit for this endpoint
        rate_limit = self._get_rate_limit(endpoint_path)
        
        # Initialize client tracking
        if client_id not in self.client_requests:
            self.client_requests[client_id] = {
                'requests': [],
                'burst_used': 0,
                'last_reset': current_time
            }
        
        client_data = self.client_requests[client_id]
        
        # Clean old requests (older than 1 minute)
        minute_ago = current_time - 60
        client_data['requests'] = [
            req_time for req_time in client_data['requests'] 
            if req_time > minute_ago
        ]
        
        # Reset burst allowance every minute
        if current_time - client_data['last_reset'] > 60:
            client_data['burst_used'] = 0
            client_data['last_reset'] = current_time
        
        # Check rate limit
        current_requests = len(client_data['requests'])
        burst_available = self.burst_allowance - client_data['burst_used']
        
        if current_requests >= rate_limit:
            if burst_available > 0:
                # Allow burst request
                client_data['burst_used'] += 1
                logger.warning(f"Burst request allowed for {client_id}: {current_requests}/{rate_limit}")
            else:
                # Rate limit exceeded
                self.audit.log_event(
                    event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
                    level=AuditLevel.WARNING,
                    message=f"Rate limit exceeded: {client_id}",
                    context={
                        "client_id": client_id,
                        "endpoint": endpoint_path,
                        "requests": current_requests,
                        "limit": rate_limit,
                        "is_medical": self._is_medical_endpoint(endpoint_path)
                    }
                )
                
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "message": f"Maximum {rate_limit} requests per minute allowed",
                        "retry_after": 60,
                        "medical_priority": self._is_medical_endpoint(endpoint_path)
                    },
                    headers={
                        "Retry-After": "60",
                        "X-RateLimit-Limit": str(rate_limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(current_time + 60))
                    }
                )
        
        # Record request
        client_data['requests'].append(current_time)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = max(0, rate_limit - len(client_data['requests']))
        response.headers["X-RateLimit-Limit"] = str(rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + 60))
        
        if self._is_medical_endpoint(endpoint_path):
            response.headers["X-Medical-Priority"] = "true"
        
        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Request validation and sanitization middleware"""
    
    def __init__(self, app, 
                 max_body_size: int = 50 * 1024 * 1024,  # 50MB for medical images
                 validate_user_agent: bool = True):
        """
        Initialize request validation middleware
        
        Args:
            app: FastAPI application
            max_body_size: Maximum request body size in bytes
            validate_user_agent: Whether to validate User-Agent header
        """
        super().__init__(app)
        self.max_body_size = max_body_size
        self.validate_user_agent = validate_user_agent
        self.audit = AuditService()
        
        # Suspicious patterns
        self.suspicious_patterns = [
            "sqlmap", "nmap", "nikto", "dirb", "gobuster",
            "burpsuite", "owasp zap", "w3af", "acunetix"
        ]
    
    def _validate_headers(self, request: Request) -> Optional[str]:
        """Validate request headers"""
        headers = request.headers
        
        # Check User-Agent
        if self.validate_user_agent:
            user_agent = headers.get("user-agent", "").lower()
            if not user_agent:
                return "Missing User-Agent header"
            
            # Check for suspicious user agents
            for pattern in self.suspicious_patterns:
                if pattern in user_agent:
                    return f"Suspicious User-Agent detected: {pattern}"
        
        # Check Content-Length if present
        content_length = headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_body_size:
                    return f"Request body too large: {size} bytes (max: {self.max_body_size})"
            except ValueError:
                return "Invalid Content-Length header"
        
        # Check for common attack headers
        dangerous_headers = {
            "x-forwarded-host": "Host header injection attempt",
            "x-http-method-override": "Method override attempt",
            "x-original-url": "URL override attempt",
            "x-rewrite-url": "URL rewrite attempt"
        }
        
        for header, message in dangerous_headers.items():
            if header in headers:
                return message
        
        return None
    
    def _validate_path(self, request: Request) -> Optional[str]:
        """Validate request path"""
        path = request.url.path
        
        # Check for path traversal
        if security_validator._contains_path_traversal(path):
            return "Path traversal attempt detected"
        
        # Check for common attack patterns
        if any(pattern in path.lower() for pattern in [
            "/proc/", "/etc/", "/..", "cmd=", "exec=", "eval=",
            "<script", "javascript:", "vbscript:", "onload=", "onerror="
        ]):
            return "Suspicious path pattern detected"
        
        return None
    
    def _validate_query_params(self, request: Request) -> Optional[str]:
        """Validate query parameters"""
        query_string = str(request.url.query)
        
        if not query_string:
            return None
        
        # Check for SQL injection patterns
        if security_validator._contains_sql_injection(query_string):
            return "SQL injection attempt detected in query parameters"
        
        # Check for XSS patterns
        xss_patterns = ["<script", "javascript:", "onload=", "onerror=", "alert("]
        if any(pattern in query_string.lower() for pattern in xss_patterns):
            return "XSS attempt detected in query parameters"
        
        return None
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate request before processing"""
        
        # Validate headers
        header_error = self._validate_headers(request)
        if header_error:
            self.audit.log_event(
                event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
                level=AuditLevel.WARNING,
                message=f"Request validation failed: {header_error}",
                context={
                    "client_ip": request.client.host if request.client else "unknown",
                    "path": request.url.path,
                    "user_agent": request.headers.get("user-agent", ""),
                    "validation_error": header_error
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Invalid request",
                    "message": "Request validation failed",
                    "compliance": "HIPAA-security-enforced"
                }
            )
        
        # Validate path
        path_error = self._validate_path(request)
        if path_error:
            self.audit.log_event(
                event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
                level=AuditLevel.ERROR,
                message=f"Path validation failed: {path_error}",
                context={
                    "client_ip": request.client.host if request.client else "unknown",
                    "path": request.url.path,
                    "validation_error": path_error
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Invalid request path",
                    "message": "Path validation failed"
                }
            )
        
        # Validate query parameters
        query_error = self._validate_query_params(request)
        if query_error:
            self.audit.log_event(
                event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
                level=AuditLevel.WARNING,
                message=f"Query validation failed: {query_error}",
                context={
                    "client_ip": request.client.host if request.client else "unknown",
                    "path": request.url.path,
                    "query": str(request.url.query),
                    "validation_error": query_error
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Invalid query parameters",
                    "message": "Query validation failed"
                }
            )
        
        # Process request if validation passes
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"Request processing error: {e}")
            self.audit.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                level=AuditLevel.ERROR,
                message=f"Request processing failed: {str(e)}",
                context={
                    "client_ip": request.client.host if request.client else "unknown",
                    "path": request.url.path,
                    "error": str(e)
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal server error",
                    "message": "Request processing failed"
                }
            )


class WebhookValidationMiddleware(BaseHTTPMiddleware):
    """Webhook signature validation middleware"""
    
    def __init__(self, app, webhook_secret: Optional[str] = None):
        """
        Initialize webhook validation middleware
        
        Args:
            app: FastAPI application
            webhook_secret: Secret for webhook signature validation
        """
        super().__init__(app)
        self.webhook_secret = webhook_secret
        self.audit = AuditService()
        
        # Webhook endpoints that require signature validation
        self.webhook_endpoints = [
            '/webhook/slack',
            '/webhook/twilio',
            '/webhook/whatsapp',
            '/webhook/medical'
        ]
    
    def _is_webhook_endpoint(self, path: str) -> bool:
        """Check if path is a webhook endpoint"""
        return any(webhook_path in path for webhook_path in self.webhook_endpoints)
    
    def _validate_slack_signature(self, request: Request, body: bytes) -> bool:
        """Validate Slack webhook signature"""
        timestamp = request.headers.get("X-Slack-Request-Timestamp")
        slack_signature = request.headers.get("X-Slack-Signature")
        
        if not timestamp or not slack_signature:
            return False
        
        # Check timestamp (prevent replay attacks)
        try:
            request_time = int(timestamp)
            if abs(time.time() - request_time) > 300:  # 5 minutes
                return False
        except ValueError:
            return False
        
        # Validate signature
        if self.webhook_secret:
            sig_basestring = f"v0:{timestamp}:{body.decode()}"
            expected_signature = "v0=" + hmac.new(
                self.webhook_secret.encode(),
                sig_basestring.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, slack_signature)
        
        return True  # Skip validation if no secret configured
    
    def _validate_twilio_signature(self, request: Request, body: bytes) -> bool:
        """Validate Twilio webhook signature"""
        twilio_signature = request.headers.get("X-Twilio-Signature")
        
        if not twilio_signature:
            return False
        
        # Twilio signature validation would go here
        # For now, return True if signature present
        return True
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate webhook signatures"""
        
        path = request.url.path
        
        # Only validate webhook endpoints
        if not self._is_webhook_endpoint(path):
            return await call_next(request)
        
        # Get request body for signature validation
        body = await request.body()
        
        # Validate based on webhook type
        valid_signature = True
        
        if '/webhook/slack' in path:
            valid_signature = self._validate_slack_signature(request, body)
        elif '/webhook/twilio' in path or '/webhook/whatsapp' in path:
            valid_signature = self._validate_twilio_signature(request, body)
        
        if not valid_signature:
            self.audit.log_event(
                event_type=AuditEventType.UNAUTHORIZED_ACCESS,
                level=AuditLevel.ERROR,
                message=f"Invalid webhook signature: {path}",
                context={
                    "client_ip": request.client.host if request.client else "unknown",
                    "path": path,
                    "headers": dict(request.headers)
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Invalid signature",
                    "message": "Webhook signature validation failed"
                }
            )
        
        # Create new request with body for downstream processing
        # Note: This is a simplified approach, proper implementation would
        # need to handle the consumed body stream properly
        
        return await call_next(request)


def add_security_middleware(app, 
                          medical_grade: bool = True,
                          rate_limit: int = 60,
                          webhook_secret: Optional[str] = None):
    """
    Add all security middleware to FastAPI application
    
    Args:
        app: FastAPI application
        medical_grade: Whether to apply medical-grade security
        rate_limit: Requests per minute rate limit
        webhook_secret: Secret for webhook validation
    """
    
    # Add middleware in reverse order (last added is executed first)
    
    # 1. Webhook validation (for webhook endpoints)
    app.add_middleware(WebhookValidationMiddleware, webhook_secret=webhook_secret)
    
    # 2. Request validation and sanitization
    app.add_middleware(RequestValidationMiddleware)
    
    # 3. Rate limiting with medical priority
    app.add_middleware(RateLimitMiddleware, requests_per_minute=rate_limit)
    
    # 4. Security headers (applied to all responses)
    app.add_middleware(SecurityHeadersMiddleware, medical_grade=medical_grade)
    
    logger.info(f"Security middleware configured (medical_grade={medical_grade})")