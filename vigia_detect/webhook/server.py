"""
Webhook server for receiving and processing medical detection events.
"""

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.base import BaseHTTPMiddleware
from typing import Dict, Any, Optional, Callable
import logging
from datetime import datetime
import asyncio
from functools import wraps

from .models import WebhookEvent, EventType, DetectionPayload, Detection, Severity
from ..utils.rate_limiter import rate_limit_fastapi, add_rate_limit_headers


logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to add rate limit headers to responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        return add_rate_limit_headers(response, request)


class WebhookServer:
    """Server for receiving webhook events."""
    
    def __init__(self, port: int = 8000, api_key: Optional[str] = None):
        """
        Initialize webhook server.
        
        Args:
            port: Port to run the server on
            api_key: Optional API key for authentication
        """
        self.port = port
        self.api_key = api_key
        self.app = FastAPI(title="Vigia Webhook Server", version="1.0.0")
        self.event_handlers: Dict[EventType, list[Callable]] = {}
        
        # Add rate limiting middleware
        self.app.add_middleware(RateLimitMiddleware)
        
        self._setup_routes()
        
    def _verify_api_key(self, authorization: Optional[str] = Header(None)) -> bool:
        """Verify API key if configured."""
        if not self.api_key:
            return True
            
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header required")
            
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization format")
            
        token = authorization[7:]
        if token != self.api_key:
            raise HTTPException(status_code=401, detail="Invalid API key")
            
        return True
        
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.post("/webhook")
        async def receive_webhook(
            event_data: Dict[str, Any],
            request: Request,
            authorized: bool = Depends(self._verify_api_key),
            rate_limited: bool = Depends(rate_limit_fastapi(limit=60, window=60))
        ):
            """Main webhook endpoint."""
            try:
                # Parse event type
                event_type_str = event_data.get('event_type')
                if not event_type_str:
                    raise HTTPException(status_code=400, detail="Missing event_type")
                    
                try:
                    event_type = EventType(event_type_str)
                except ValueError:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Invalid event_type: {event_type_str}"
                    )
                    
                # Process event
                result = await self._process_event(event_type, event_data)
                
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": True,
                        "message": "Event processed successfully",
                        "data": result
                    }
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error processing webhook: {str(e)}")
                raise HTTPException(status_code=500, detail="Internal server error")
                
        @self.app.get("/health")
        async def health_check(
            request: Request,
            rate_limited: bool = Depends(rate_limit_fastapi(limit=120, window=60))
        ):
            """Health check endpoint."""
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0"
            }
            
        @self.app.get("/webhook/events")
        async def list_events(
            request: Request,
            authorized: bool = Depends(self._verify_api_key),
            rate_limited: bool = Depends(rate_limit_fastapi(limit=30, window=60))
        ):
            """List registered event types."""
            return {
                "events": [event.value for event in EventType],
                "handlers": {
                    event.value: len(handlers) 
                    for event, handlers in self.event_handlers.items()
                }
            }
            
    async def _process_event(self, event_type: EventType, event_data: Dict[str, Any]) -> Any:
        """
        Process incoming webhook event.
        
        Args:
            event_type: Type of event
            event_data: Raw event data
            
        Returns:
            Processing result
        """
        handlers = self.event_handlers.get(event_type, [])
        
        if not handlers:
            logger.warning(f"No handlers registered for {event_type.value}")
            return {"warning": "No handlers for this event type"}
            
        # Convert payload based on event type
        payload = event_data.get('payload', {})
        
        if event_type == EventType.DETECTION_COMPLETED:
            # Just pass the payload as dict for flexibility
            payload_obj = payload
        else:
            payload_obj = payload
            
        # Run all handlers
        results = []
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(event_type, payload_obj)
                else:
                    result = handler(event_type, payload_obj)
                results.append(result)
            except Exception as e:
                logger.error(f"Handler error: {str(e)}")
                results.append({"error": str(e)})
                
        return {"processed_by": len(handlers), "results": results}
        
    def on_event(self, event_type: EventType):
        """
        Decorator to register event handlers.
        
        Usage:
            @webhook_server.on_event(EventType.DETECTION_COMPLETED)
            async def handle_detection(event_type, payload):
                # Process detection
                pass
        """
        def decorator(func: Callable):
            if event_type not in self.event_handlers:
                self.event_handlers[event_type] = []
            self.event_handlers[event_type].append(func)
            return func
        return decorator
        
    def register_handler(self, event_type: EventType, handler: Callable):
        """
        Register an event handler programmatically.
        
        Args:
            event_type: Event type to handle
            handler: Handler function
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        
    def get_app(self) -> FastAPI:
        """Get FastAPI app instance."""
        return self.app
    
    def run(self, host: str = "0.0.0.0", port: Optional[int] = None):
        """
        Run the webhook server.
        
        Args:
            host: Host to bind to
            port: Port to bind to (uses self.port if not specified)
        """
        import uvicorn
        uvicorn.run(self.app, host=host, port=port or self.port)