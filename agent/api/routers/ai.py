"""
FastAPI router for AI-powered trip generation endpoints.

Handles:
- Destination recommendation generation
- Itinerary generation
- Itinerary regeneration with feedback

Per plan_PROGRESS.md Task 3.6.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from ..middleware.auth import get_current_user, TokenData
from ..database import (
    is_user_trip_member,
    is_user_trip_organizer,
    get_trip_by_id
)
from ..models.recommendations import (
    GenerateRecommendationsRequest,
    GenerateRecommendationsResponse
)
from ..models.itinerary import (
    GenerateItineraryRequest,
    GenerateItineraryResponse,
    RegenerateItineraryRequest
)
from ..services.agent_service import get_agent_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ai",
    tags=["AI Generation"],
    dependencies=[Depends(get_current_user)]
)


@router.post("/recommendations/generate", response_model=GenerateRecommendationsResponse)
async def generate_recommendations(
    request: GenerateRecommendationsRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Generate destination recommendations for a trip.

    Requires:
    - User must be a member of the trip
    - At least one member must have submitted preferences
    - Trip must be in 'collecting' or 'recommending' status

    Returns 3-5 destination recommendations based on aggregated group preferences.
    """
    trip_id = str(request.trip_id)
    user_id = current_user.user_id

    # Authorization: Check if user is trip member
    if not await is_user_trip_member(user_id, trip_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member of this trip to generate recommendations"
        )

    # Get trip to check status
    trip = await get_trip_by_id(trip_id)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )

    # Check trip status
    trip_status = trip.get("status")
    if trip_status not in ["collecting", "recommending"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot generate recommendations for trip in '{trip_status}' status. Trip must be in 'collecting' or 'recommending' status."
        )

    # Generate recommendations using agent service
    agent_service = get_agent_service()
    result = await agent_service.generate_recommendations(trip_id, user_id)

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Unknown error during recommendation generation")
        )

    recommendations_data = result.get("recommendations", {})

    # Build response
    return GenerateRecommendationsResponse(
        trip_id=request.trip_id,
        destinations=recommendations_data.get("options", []),
        generated_at=result.get("generated_at", ""),
        aggregated_preferences_summary=recommendations_data.get("group_summary")
    )


@router.post("/itinerary/generate", response_model=GenerateItineraryResponse)
async def generate_itinerary(
    request: GenerateItineraryRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Generate a full itinerary for a trip.

    Requires:
    - User must be a member of the trip
    - Trip must have a destination selected (status: 'planning')
    - Preferences must be submitted

    Returns a day-by-day itinerary with morning/afternoon/evening activities,
    costs, locations, and tips.
    """
    trip_id = str(request.trip_id)
    user_id = current_user.user_id

    # Authorization: Check if user is trip member
    if not await is_user_trip_member(user_id, trip_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member of this trip to generate an itinerary"
        )

    # Get trip to check status
    trip = await get_trip_by_id(trip_id)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )

    # Check trip status
    trip_status = trip.get("status")
    if trip_status != "planning":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot generate itinerary for trip in '{trip_status}' status. Trip must be in 'planning' status (destination selected)."
        )

    # Generate itinerary using agent service
    agent_service = get_agent_service()
    result = await agent_service.generate_itinerary(
        trip_id,
        request.destination_name,
        user_id
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Unknown error during itinerary generation")
        )

    itinerary_data = result.get("itinerary", {})

    # Build response
    return GenerateItineraryResponse(
        trip_id=request.trip_id,
        destination_name=request.destination_name,
        days=itinerary_data.get("days", []),
        total_cost=itinerary_data.get("total_cost", 0),
        trip_length_days=len(itinerary_data.get("days", [])),
        generated_at=result.get("generated_at", ""),
        summary=itinerary_data.get("assumptions", "")
    )


@router.post("/itinerary/regenerate", response_model=GenerateItineraryResponse)
async def regenerate_itinerary(
    request: RegenerateItineraryRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Regenerate itinerary with user feedback.

    Requires:
    - User must be a member of the trip
    - Trip must have an existing itinerary
    - Feedback must be provided (1-1000 characters)

    Incorporates user feedback into a new itinerary version.
    Maximum 5 regenerations to prevent infinite loops.
    """
    trip_id = str(request.trip_id)
    user_id = current_user.user_id

    # Authorization: Check if user is trip member
    if not await is_user_trip_member(user_id, trip_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member of this trip to regenerate the itinerary"
        )

    # Get trip to check status
    trip = await get_trip_by_id(trip_id)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )

    # Check trip status - allow regeneration in 'planning' status only
    trip_status = trip.get("status")
    if trip_status != "planning":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot regenerate itinerary for trip in '{trip_status}' status. Trip must be in 'planning' status."
        )

    # Regenerate itinerary using agent service
    agent_service = get_agent_service()
    result = await agent_service.regenerate_itinerary(
        trip_id,
        request.feedback,
        user_id,
        request.regeneration_count or 0
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Unknown error during itinerary regeneration")
        )

    itinerary_data = result.get("itinerary", {})

    # Build response
    return GenerateItineraryResponse(
        trip_id=request.trip_id,
        destination_name=itinerary_data.get("destination_name", ""),
        days=itinerary_data.get("days", []),
        total_cost=itinerary_data.get("total_cost", 0),
        trip_length_days=len(itinerary_data.get("days", [])),
        generated_at=result.get("generated_at", ""),
        summary=f"Regenerated (iteration {result.get('regeneration_count', 1)}): {itinerary_data.get('assumptions', '')}"
    )
