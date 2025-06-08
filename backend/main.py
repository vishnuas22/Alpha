from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import structlog
import uvicorn
import time
from contextlib import asynccontextmanager

# Import configuration and core modules
from config import settings
from database import connect_to_mongo, close_mongo_connection
from rate_limiter import limiter, cleanup_expired_rate_limits

# Import route modules
from routes import auth_routes, chat_routes, file_routes, websocket_routes, admin_routes

# Configure structured logging
structlog.configure(
    processors=[
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Alpha ChatGPT Backend...")
    
    # Connect to MongoDB
    await connect_to_mongo()
    
    # Start background tasks
    import asyncio
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
    logger.info("Alpha ChatGPT Backend started successfully!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Alpha ChatGPT Backend...")
    
    # Cancel background tasks
    cleanup_task.cancel()
    
    # Close database connection
    await close_mongo_connection()
    
    logger.info("Alpha ChatGPT Backend shutdown complete!")

# Create FastAPI application
app = FastAPI(
    title="Alpha ChatGPT API",
    description="Comprehensive ChatGPT clone backend with AI integration",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    if settings.debug:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal server error",
                "details": str(exc)
            }
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal server error"
            }
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Alpha ChatGPT API",
        "version": "1.0.0",
        "docs": "/docs" if settings.debug else "Documentation disabled in production"
    }

# API endpoint for frontend compatibility
@app.get("/api")
async def api_root():
    """API root endpoint for frontend compatibility"""
    return {
        "message": "Alpha ChatGPT API v1.0.0",
        "status": "operational"
    }

# Include routers
app.include_router(auth_routes.router, prefix="/api")
app.include_router(chat_routes.router, prefix="/api")
app.include_router(file_routes.router, prefix="/api")
app.include_router(admin_routes.router, prefix="/api")
app.include_router(websocket_routes.router, prefix="/api")

# Background tasks
async def periodic_cleanup():
    """Periodic cleanup tasks"""
    import asyncio
    from file_service import file_service
    
    while True:
        try:
            # Wait 1 hour between cleanup runs
            await asyncio.sleep(3600)
            
            logger.info("Running periodic cleanup...")
            
            # Cleanup expired rate limits
            await cleanup_expired_rate_limits()
            
            # Cleanup orphaned files
            await file_service.cleanup_orphaned_files()
            
            logger.info("Periodic cleanup completed")
            
        except asyncio.CancelledError:
            logger.info("Cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")

# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests"""
    start_time = time.time()
    
    # Skip logging for health checks and static files
    if request.url.path in ["/health", "/favicon.ico"]:
        return await call_next(request)
    
    logger.info(
        f"Request started",
        method=request.method,
        path=request.url.path,
        client_ip=get_remote_address(request)
    )
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    logger.info(
        f"Request completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        process_time=f"{process_time:.3f}s"
    )
    
    return response

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.debug,
        access_log=settings.debug
    )