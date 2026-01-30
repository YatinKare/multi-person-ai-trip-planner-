"""
Data access tools for TripSync agents.

These FunctionTools provide agents with access to database operations
for loading trip context, preferences, and storing results.

Per plan_AGENTS.md Section 8.1.
"""
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv
from pathlib import Path
from supabase import create_client, Client

# Load environment variables
project_root = Path(__file__).parent.parent.parent
env_path = project_root / ".env.local"
load_dotenv(env_path)

# Get Supabase credentials
SUPABASE_URL = os.getenv("PUBLIC_SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("PRIVATE_SUPABASE_SERVICE_ROLE")

_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Get or create Supabase client instance."""
    global _supabase_client
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError("Supabase credentials not configured")
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return _supabase_client


def load_trip_context(trip_id: str) -> Dict[str, Any]:
    """
    Load trip context including trip details and members.

    Args:
        trip_id: UUID of the trip

    Returns:
        dict: Trip context with trip data and member list
    """
    try:
        client = get_supabase_client()

        # Get trip data
        trip_result = client.table("trips").select("*").eq("id", trip_id).execute()
        if not trip_result.data:
            return {"error": f"Trip {trip_id} not found"}

        trip_data = trip_result.data[0]

        # Get members
        members_result = client.table("trip_members").select("*, profiles(*)").eq("trip_id", trip_id).execute()
        members = members_result.data if members_result.data else []

        return {
            "trip_id": trip_id,
            "trip_name": trip_data.get("name"),
            "status": trip_data.get("status"),
            "rough_timeframe": trip_data.get("rough_timeframe"),
            "created_at": trip_data.get("created_at"),
            "members": members,
            "member_count": len(members)
        }
    except Exception as e:
        return {"error": f"Failed to load trip context: {str(e)}"}


def load_member_preferences(trip_id: str) -> List[Dict[str, Any]]:
    """
    Load all member preferences for a trip.

    Args:
        trip_id: UUID of the trip

    Returns:
        list: List of preference records (JSONB data + metadata)
    """
    try:
        client = get_supabase_client()
        result = client.table("preferences").select("*").eq("trip_id", trip_id).execute()

        if not result.data:
            return []

        return result.data
    except Exception as e:
        return [{"error": f"Failed to load preferences: {str(e)}"}]


def load_existing_recommendations(trip_id: str) -> Optional[Dict[str, Any]]:
    """
    Load existing recommendations for a trip if they exist.

    Args:
        trip_id: UUID of the trip

    Returns:
        dict or None: Most recent recommendations record
    """
    try:
        client = get_supabase_client()
        result = client.table("recommendations").select("*").eq("trip_id", trip_id).order("generated_at", desc=True).limit(1).execute()

        if not result.data:
            return None

        return result.data[0]
    except Exception as e:
        return {"error": f"Failed to load recommendations: {str(e)}"}


def load_existing_itinerary(trip_id: str) -> Optional[Dict[str, Any]]:
    """
    Load existing itinerary for a trip if it exists.

    Args:
        trip_id: UUID of the trip

    Returns:
        dict or None: Existing itinerary record
    """
    try:
        client = get_supabase_client()
        result = client.table("itineraries").select("*").eq("trip_id", trip_id).limit(1).execute()

        if not result.data:
            return None

        return result.data[0]
    except Exception as e:
        return {"error": f"Failed to load itinerary: {str(e)}"}


def store_recommendations(trip_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Store generated recommendations in the database.

    Args:
        trip_id: UUID of the trip
        payload: RecommendationsPack data (already validated)

    Returns:
        dict: Success status and record ID
    """
    try:
        client = get_supabase_client()

        # Extract user_id from payload if available, otherwise use system
        generated_by = payload.get("generated_by")

        # Store in recommendations table
        insert_data = {
            "trip_id": trip_id,
            "destinations": payload.get("options", []),
            "generated_by": generated_by
        }

        result = client.table("recommendations").insert(insert_data).execute()

        if not result.data:
            return {"success": False, "error": "Failed to insert recommendations"}

        return {
            "success": True,
            "recommendation_id": result.data[0].get("id"),
            "generated_at": result.data[0].get("generated_at")
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to store recommendations: {str(e)}"}


def store_itinerary(trip_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Store generated itinerary in the database.

    Args:
        trip_id: UUID of the trip
        payload: Itinerary data (already validated)

    Returns:
        dict: Success status and record ID
    """
    try:
        client = get_supabase_client()

        # Extract key fields
        destination_name = payload.get("destination_name", "Unknown")
        days = payload.get("days", [])
        total_cost = payload.get("total_cost", 0)
        generated_by = payload.get("generated_by")

        # Store in itineraries table
        insert_data = {
            "trip_id": trip_id,
            "destination_name": destination_name,
            "days": days,
            "total_cost": total_cost,
            "generated_by": generated_by
        }

        result = client.table("itineraries").insert(insert_data).execute()

        if not result.data:
            return {"success": False, "error": "Failed to insert itinerary"}

        return {
            "success": True,
            "itinerary_id": result.data[0].get("id"),
            "generated_at": result.data[0].get("generated_at")
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to store itinerary: {str(e)}"}


def store_progress(trip_id: str, message: str, stage: str) -> Dict[str, Any]:
    """
    Store progress event for long-running operations (optional/future feature).

    Args:
        trip_id: UUID of the trip
        message: Progress message
        stage: Current stage name

    Returns:
        dict: Success status
    """
    # For now, just log to console
    # In the future, could store in a progress_events table
    print(f"[Progress - {trip_id}] {stage}: {message}")
    return {"success": True, "message": message, "stage": stage}
