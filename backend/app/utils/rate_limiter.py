"""
Rate limiting middleware and utilities.
"""
import time
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, requests_limit: int, window_seconds: int):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, key: str) -> Tuple[bool, int]:
        """
        Check if request is allowed for the given key.
        
        Args:
            key: Identifier for rate limiting (e.g., IP address)
            
        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > window_start
        ]
        
        # Check limit
        if len(self.requests[key]) >= self.requests_limit:
            return False, 0
        
        # Add current request
        self.requests[key].append(now)
        remaining = self.requests_limit - len(self.requests[key])
        
        return True, remaining


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for FastAPI."""
    
    def __init__(self, app, requests_limit: int = None, window_seconds: int = None):
        super().__init__(app)
        self.limiter = RateLimiter(
            requests_limit=requests_limit or settings.RATE_LIMIT_REQUESTS,
            window_seconds=window_seconds or settings.RATE_LIMIT_WINDOW
        )
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Skip rate limiting for health check
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Check rate limit
        is_allowed, remaining = self.limiter.is_allowed(client_ip)
        
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Add rate limit headers
        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Limit"] = str(self.limiter.requests_limit)
        
        return response
