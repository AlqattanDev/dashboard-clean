"""
Clean Operations Dashboard Backend
FastAPI application with JWT authentication and MongoDB
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
# Rate limiting imports
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pathlib import Path
import uvicorn
from loguru import logger

# Import configuration and services
from config import settings
from services.database import db
from services.user_service import create_default_admin
from services.function_service import create_sample_functions
from api.auth import router as auth_router
from api.users import router as users_router
from api.functions import router as functions_router
from api.requests import router as requests_router
from api.dashboard import router as dashboard_router

# Create FastAPI app
app = FastAPI(
    title="Operations Dashboard",
    description="Clean operations dashboard with JWT authentication",
    version="3.0.0"
)

# Rate limiting configuration
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize database and create default data"""
    try:
        # Connect to database
        logger.info("Connecting to MongoDB...")
        db.connect(settings.mongodb_url, settings.database_name)
        logger.info("Database connected successfully")
        
        # Create default admin user
        logger.info("Creating default admin user...")
        create_default_admin()
        
        # Create sample functions
        logger.info("Creating sample functions...")
        create_sample_functions()
        
        logger.info("Application startup complete")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up database connections"""
    try:
        db.close()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

# Include API routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(functions_router)
app.include_router(requests_router)
app.include_router(dashboard_router)

# Get paths
backend_dir = Path(__file__).parent
project_dir = backend_dir.parent
frontend_assets = project_dir / "frontend" / "assets"

# Mount static files
app.mount("/static", StaticFiles(directory=str(frontend_assets)), name="static")

# Serve frontend for all main routes
@app.get("/")
async def root():
    return FileResponse(str(frontend_assets / "index.html"))

@app.get("/dashboard")
async def dashboard():
    return FileResponse(str(frontend_assets / "index.html"))

@app.get("/login") 
async def login_page():
    return FileResponse(str(frontend_assets / "index.html"))

@app.get("/functions")
async def functions_page():
    return FileResponse(str(frontend_assets / "index.html"))

@app.get("/users")
async def users_page():
    return FileResponse(str(frontend_assets / "index.html"))

@app.get("/requests")
async def requests_page():
    return FileResponse(str(frontend_assets / "index.html"))

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint with database status"""
    try:
        # Simple database check
        db.users.count_documents({}, limit=1)
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    return {
        "status": "healthy",
        "service": "dashboard-backend",
        "version": "3.0.0",
        "database": db_status,
        "authentication": "jwt",
        "ldap_enabled": settings.ldap_enabled
    }

# API information
@app.get("/api")
async def api_info():
    """API information endpoint"""
    return {
        "service": "Operations Dashboard API",
        "version": "3.0.0",
        "docs": "/docs",
        "endpoints": {
            "authentication": "/api/v1/auth",
            "users": "/api/v1/users",
            "functions": "/api/v1/functions",
            "requests": "/api/v1/requests",
            "health": "/health"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )