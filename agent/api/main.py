"""
TripSync FastAPI Application

Main entry point for the FastAPI backend that handles:
- AI destination recommendations via Google ADK
- AI itinerary generation via Google ADK
- Preference aggregation
- JWT token validation from Supabase Auth
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

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
    return {
        "status": "healthy",
        "api": "operational",
        "database": "not_yet_implemented",
        "ai": "not_yet_implemented"
    }


# Future router includes will go here
# Example:
# from api.routers import recommendations, itineraries
# app.include_router(recommendations.router, prefix="/api/trips", tags=["recommendations"])
# app.include_router(itineraries.router, prefix="/api/trips", tags=["itineraries"])
