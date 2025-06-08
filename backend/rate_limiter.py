import time
from typing import Optional
from datetime import datetime, timedelta
import structlog
from fastapi import HTTPException, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from config import settings
from database import get_database

logger = structlog.get_logger()

# Create limiter instance
limiter = Limiter(key_func=get_remote_address)

class AdvancedRateLimiter:
    def __init__(self):
        self.db = None
    
    async def init_db(self):
        """Initialize database connection"""
        if not self.db:
            self.db = get_database()
    
    async def check_rate_limit(
        self, 
        key: str, 
        limit: int, 
        window_seconds: int,
        identifier: str = "general"
    ) -> bool:
        """
        Check if a request is within rate limits
        
        Args:
            key: Unique identifier for the rate limit (e.g., user_id, ip_address)
            limit: Maximum number of requests allowed
            window_seconds: Time window in seconds
            identifier: Type of rate limit being checked
            
        Returns:
            True if within limits, False if exceeded
        """
        await self.init_db()
        
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)
        
        # Clean up old entries
        await self.db.rate_limits.delete_many({
            "key": key,
            "identifier": identifier,
            "timestamp": {"$lt": window_start}
        })
        
        # Count current requests in window
        current_count = await self.db.rate_limits.count_documents({
            "key": key,
            "identifier": identifier,
            "timestamp": {"$gte": window_start}
        })
        
        if current_count >= limit:
            logger.warning(f"Rate limit exceeded for {key}: {current_count}/{limit}")
            return False
        
        # Record this request
        await self.db.rate_limits.insert_one({
            "key": key,
            "identifier": identifier,
            "timestamp": now,
            "expires_at": now + timedelta(seconds=window_seconds)
        })
        
        return True
    
    async def get_remaining_requests(
        self, 
        key: str, 
        limit: int, 
        window_seconds: int,
        identifier: str = "general"
    ) -> tuple[int, int]:
        """
        Get remaining requests and reset time
        
        Returns:
            (remaining_requests, reset_time_seconds)
        """
        await self.init_db()
        
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)
        
        # Count current requests
        current_count = await self.db.rate_limits.count_documents({
            "key": key,
            "identifier": identifier,
            "timestamp": {"$gte": window_start}
        })
        
        remaining = max(0, limit - current_count)
        
        # Find the oldest request in current window to calculate reset time
        oldest_request = await self.db.rate_limits.find_one(
            {
                "key": key,
                "identifier": identifier,
                "timestamp": {"$gte": window_start}
            },
            sort=[("timestamp", 1)]
        )
        
        if oldest_request:
            reset_time = int((oldest_request["timestamp"] + timedelta(seconds=window_seconds) - now).total_seconds())
        else:
            reset_time = 0
        
        return remaining, max(0, reset_time)

# Global rate limiter instance
advanced_rate_limiter = AdvancedRateLimiter()

async def check_user_rate_limits(user_id: str, request_type: str = "general") -> bool:
    """Check rate limits for authenticated users"""
    
    # Different limits based on request type
    limits = {
        "general": (settings.rate_limit_per_minute, 60),
        "chat": (30, 60),  # 30 chat requests per minute
        "file_upload": (10, 60),  # 10 file uploads per minute
        "export": (5, 3600),  # 5 exports per hour
    }
    
    limit, window = limits.get(request_type, (60, 60))
    
    return await advanced_rate_limiter.check_rate_limit(
        key=f"user:{user_id}",
        limit=limit,
        window_seconds=window,
        identifier=request_type
    )

async def check_ip_rate_limits(ip_address: str, request_type: str = "general") -> bool:
    """Check rate limits for IP addresses"""
    
    # Stricter limits for unauthenticated requests
    limits = {
        "general": (30, 60),  # 30 requests per minute
        "auth": (10, 60),     # 10 auth attempts per minute
        "registration": (3, 3600),  # 3 registrations per hour
    }
    
    limit, window = limits.get(request_type, (30, 60))
    
    return await advanced_rate_limiter.check_rate_limit(
        key=f"ip:{ip_address}",
        limit=limit,
        window_seconds=window,
        identifier=request_type
    )

def rate_limit_decorator(request_type: str = "general"):
    """Decorator for rate limiting endpoints"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract request and user info from kwargs
            request = None
            user = None
            
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            # Check for user in kwargs
            if 'current_user' in kwargs:
                user = kwargs['current_user']
            
            if not request:
                # If no request object, skip rate limiting
                return await func(*args, **kwargs)
            
            ip_address = get_remote_address(request)
            
            # Check IP rate limits
            ip_allowed = await check_ip_rate_limits(ip_address, request_type)
            if not ip_allowed:
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests from this IP address",
                    headers={"Retry-After": "60"}
                )
            
            # Check user rate limits if authenticated
            if user:
                user_allowed = await check_user_rate_limits(user.id, request_type)
                if not user_allowed:
                    remaining, reset_time = await advanced_rate_limiter.get_remaining_requests(
                        f"user:{user.id}", 60, 60, request_type
                    )
                    raise HTTPException(
                        status_code=429,
                        detail="Too many requests",
                        headers={
                            "Retry-After": str(reset_time),
                            "X-RateLimit-Remaining": str(remaining)
                        }
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

async def cleanup_expired_rate_limits():
    """Cleanup expired rate limit entries"""
    db = get_database()
    result = await db.rate_limits.delete_many({
        "expires_at": {"$lt": datetime.utcnow()}
    })
    if result.deleted_count > 0:
        logger.info(f"Cleaned up {result.deleted_count} expired rate limit entries")