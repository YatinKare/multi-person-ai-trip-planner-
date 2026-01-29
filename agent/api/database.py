"""
Database connection and utility functions for FastAPI backend.

This module provides:
- Supabase client initialization using service role key
- Common database query helpers
- Connection pooling and error handling
"""
import os
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from project root
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
env_path = project_root / ".env.local"
load_dotenv(env_path)

# Get Supabase credentials from environment
SUPABASE_URL = os.getenv("PUBLIC_SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("PRIVATE_SUPABASE_SERVICE_ROLE")

if not SUPABASE_URL:
    raise ValueError("PUBLIC_SUPABASE_URL environment variable is required")
if not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("PRIVATE_SUPABASE_SERVICE_ROLE environment variable is required")

# Initialize Supabase client with service role key
# Service role key bypasses RLS, so we must implement authorization checks in code
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get or create a Supabase client instance.

    Uses service role key which bypasses Row Level Security (RLS).
    Authorization must be checked manually in endpoint handlers.

    Returns:
        Client: Supabase client instance
    """
    global _supabase_client

    if _supabase_client is None:
        _supabase_client = create_client(
            SUPABASE_URL,
            SUPABASE_SERVICE_ROLE_KEY
        )

    return _supabase_client


async def check_database_connection() -> bool:
    """
    Check if database connection is healthy.

    Returns:
        bool: True if connection is healthy, False otherwise
    """
    try:
        client = get_supabase_client()
        # Try a simple query to test connection
        result = client.table("profiles").select("id").limit(1).execute()
        return True
    except Exception as e:
        print(f"Database connection check failed: {e}")
        return False


# Helper functions for common database operations

async def get_trip_by_id(trip_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a trip by ID.

    Args:
        trip_id: UUID of the trip

    Returns:
        Trip data as dict, or None if not found
    """
    try:
        client = get_supabase_client()
        result = client.table("trips").select("*").eq("id", trip_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error fetching trip {trip_id}: {e}")
        return None


async def get_trip_by_invite_code(invite_code: str) -> Optional[Dict[str, Any]]:
    """
    Get a trip by invite code.

    Args:
        invite_code: Unique invite code for the trip

    Returns:
        Trip data as dict, or None if not found
    """
    try:
        client = get_supabase_client()
        result = client.table("trips").select("*").eq("invite_code", invite_code).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error fetching trip by invite code {invite_code}: {e}")
        return None


async def is_user_trip_member(user_id: str, trip_id: str) -> bool:
    """
    Check if a user is a member of a trip.

    Args:
        user_id: UUID of the user
        trip_id: UUID of the trip

    Returns:
        True if user is a member, False otherwise
    """
    try:
        client = get_supabase_client()
        result = client.table("trip_members").select("user_id").eq("user_id", user_id).eq("trip_id", trip_id).execute()
        return len(result.data) > 0
    except Exception as e:
        print(f"Error checking trip membership for user {user_id}, trip {trip_id}: {e}")
        return False


async def is_user_trip_organizer(user_id: str, trip_id: str) -> bool:
    """
    Check if a user is the organizer of a trip.

    Args:
        user_id: UUID of the user
        trip_id: UUID of the trip

    Returns:
        True if user is organizer, False otherwise
    """
    try:
        client = get_supabase_client()
        result = client.table("trip_members").select("role").eq("user_id", user_id).eq("trip_id", trip_id).execute()
        return len(result.data) > 0 and result.data[0].get("role") == "organizer"
    except Exception as e:
        print(f"Error checking organizer status for user {user_id}, trip {trip_id}: {e}")
        return False


async def get_trip_preferences(trip_id: str) -> List[Dict[str, Any]]:
    """
    Get all preferences for a trip.

    Args:
        trip_id: UUID of the trip

    Returns:
        List of preference records
    """
    try:
        client = get_supabase_client()
        result = client.table("preferences").select("*").eq("trip_id", trip_id).execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error fetching preferences for trip {trip_id}: {e}")
        return []


async def get_trip_members(trip_id: str) -> List[Dict[str, Any]]:
    """
    Get all members of a trip.

    Args:
        trip_id: UUID of the trip

    Returns:
        List of trip_member records with user profile data
    """
    try:
        client = get_supabase_client()
        result = client.table("trip_members").select("*, profiles(*)").eq("trip_id", trip_id).execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error fetching members for trip {trip_id}: {e}")
        return []


async def get_trip_recommendations(trip_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the most recent recommendations for a trip.

    Args:
        trip_id: UUID of the trip

    Returns:
        Recommendations record, or None if not found
    """
    try:
        client = get_supabase_client()
        result = client.table("recommendations").select("*").eq("trip_id", trip_id).order("generated_at", desc=True).limit(1).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error fetching recommendations for trip {trip_id}: {e}")
        return None


async def get_trip_itinerary(trip_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the itinerary for a trip.

    Args:
        trip_id: UUID of the trip

    Returns:
        Itinerary record, or None if not found
    """
    try:
        client = get_supabase_client()
        result = client.table("itineraries").select("*").eq("trip_id", trip_id).limit(1).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error fetching itinerary for trip {trip_id}: {e}")
        return None
