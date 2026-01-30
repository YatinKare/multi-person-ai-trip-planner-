"""
TripSync FastAPI Application

Main entry point for the FastAPI backend that handles:
- AI destination recommendations via Google ADK
- AI itinerary generation via Google ADK
- Preference aggregation
- JWT token validation from Supabase Auth
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from api.middleware import TokenData, get_current_user
from api.database import check_database_connection, get_supabase_client

# Load environment variables
load_dotenv()

# Create FastAPI app instance
app = FastAPI(
    title="TripSync API",
    description="AI-powered group trip planning backend",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Get allowed origins from environment variable
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "TripSync API",
        "version": "0.1.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    # Check database connection
    db_healthy = await check_database_connection()

    return {
        "status": "healthy" if db_healthy else "degraded",
        "api": "operational",
        "database": "operational" if db_healthy else "connection_failed",
        "ai": "not_yet_implemented"
    }


@app.get("/api/me")
async def get_current_user_info(user: TokenData = Depends(get_current_user)):
    """
    Protected endpoint that returns current user info from JWT token.
    Requires valid Authorization: Bearer <token> header.

    This endpoint demonstrates JWT validation middleware in action.
    """
    return {
        "user_id": user.user_id,
        "email": user.email,
        "role": user.role,
        "message": "Successfully authenticated"
    }


# Include routers
from api.routers import ai_router

app.include_router(ai_router, prefix="/api/trips")
