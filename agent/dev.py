#!/usr/bin/env python3
"""
Development server startup script for TripSync FastAPI backend.

This script starts the FastAPI server with hot reload enabled for development.
It configures uvicorn with appropriate settings for local development:
- Hot reload on file changes
- Detailed logging
- Configurable port via environment variable
- Proper error handling

Usage:
    uv run python dev.py
    # Or with custom port:
    FASTAPI_PORT=9000 uv run python dev.py
"""
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Load environment variables from project root
project_root = Path(__file__).parent.parent
env_file = project_root / ".env.local"

if env_file.exists():
    load_dotenv(env_file)
    logger.info(f"Loaded environment variables from {env_file}")
else:
    logger.warning(f"No .env.local file found at {env_file}")
    logger.warning("Some features may not work without proper environment configuration")

# Get configuration from environment
HOST = os.getenv("FASTAPI_HOST", "0.0.0.0")
PORT = int(os.getenv("FASTAPI_PORT", "8000"))
RELOAD = os.getenv("FASTAPI_RELOAD", "true").lower() == "true"
LOG_LEVEL = os.getenv("FASTAPI_LOG_LEVEL", "info").lower()

# Validate required environment variables
required_env_vars = [
    "PUBLIC_SUPABASE_URL",
    "PRIVATE_SUPABASE_SERVICE_ROLE",
    "SUPABASE_JWT_SECRET",
]

missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    logger.error("Missing required environment variables:")
    for var in missing_vars:
        logger.error(f"  - {var}")
    logger.error("\nPlease add these to your .env.local file")
    sys.exit(1)


def main():
    """Start the FastAPI development server."""
    try:
        import uvicorn
    except ImportError:
        logger.error("uvicorn is not installed. Please run: uv sync")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("Starting TripSync FastAPI Development Server")
    logger.info("=" * 60)
    logger.info(f"Host: {HOST}")
    logger.info(f"Port: {PORT}")
    logger.info(f"Reload: {RELOAD}")
    logger.info(f"Log Level: {LOG_LEVEL}")
    logger.info(f"Docs: http://{HOST}:{PORT}/docs")
    logger.info(f"ReDoc: http://{HOST}:{PORT}/redoc")
    logger.info("=" * 60)

    try:
        uvicorn.run(
            "api.main:app",
            host=HOST,
            port=PORT,
            reload=RELOAD,
            log_level=LOG_LEVEL,
            access_log=True,
            reload_dirs=["api"] if RELOAD else None,
        )
    except KeyboardInterrupt:
        logger.info("\nShutting down server...")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
