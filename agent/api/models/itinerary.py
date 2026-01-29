"""Pydantic models for itinerary generation."""

from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID


class Activity(BaseModel):
    """A single activity in the itinerary."""

    name: str = Field(..., description="Activity name")
    description: str = Field(..., description="Detailed activity description")
    time_slot: str = Field(
        ...,
        description="Time slot: 'morning', 'afternoon', 'evening'"
    )
    estimated_cost: float = Field(..., ge=0, description="Estimated cost per person in USD")
    location: str = Field(..., description="Location or address")
    location_url: Optional[str] = Field(None, description="Optional Google Maps or website URL")
    duration_hours: float = Field(..., gt=0, description="Estimated duration in hours")
    tips: Optional[str] = Field(None, description="Tips, notes, or recommendations")
    category: Optional[str] = Field(
        None,
        description="Category: dining, activity, transportation, accommodation, etc."
    )


class DayItinerary(BaseModel):
    """Itinerary for a single day."""

    day_number: int = Field(..., ge=1, description="Day number (1-indexed)")
    date: Optional[str] = Field(None, description="Actual date if known (ISO 8601)")
    title: Optional[str] = Field(None, description="Optional day title (e.g., 'Arrival Day', 'Beach Day')")
    activities: List[Activity] = Field(
        ...,
        description="List of activities for this day",
        min_length=1
    )
    total_cost: float = Field(..., ge=0, description="Total cost for this day")


class GenerateItineraryRequest(BaseModel):
    """Request to generate a full itinerary."""

    trip_id: UUID = Field(..., description="Trip ID to generate itinerary for")
    destination_name: str = Field(..., description="Selected destination name")
    # Additional parameters will be fetched from database:
    # - trip length (from aggregated preferences)
    # - budget (from aggregated preferences)
    # - vibes and constraints (from aggregated preferences)


class GenerateItineraryResponse(BaseModel):
    """Response containing generated itinerary."""

    trip_id: UUID = Field(..., description="Trip ID this itinerary is for")
    destination_name: str = Field(..., description="Destination name")
    days: List[DayItinerary] = Field(
        ...,
        description="Day-by-day itinerary",
        min_length=1
    )
    total_cost: float = Field(..., ge=0, description="Total estimated trip cost per person")
    trip_length_days: int = Field(..., ge=1, description="Total trip length in days")
    generated_at: str = Field(..., description="Timestamp when itinerary was generated (ISO 8601)")
    summary: Optional[str] = Field(
        None,
        description="Brief summary of the trip itinerary"
    )


class RegenerateItineraryRequest(BaseModel):
    """Request to regenerate itinerary with feedback."""

    trip_id: UUID = Field(..., description="Trip ID to regenerate itinerary for")
    feedback: str = Field(
        ...,
        description="User feedback and modification requests (e.g., 'Make it more budget-friendly', 'Add more outdoor activities')",
        min_length=1,
        max_length=1000
    )
    regeneration_count: Optional[int] = Field(
        None,
        description="Current regeneration count (used internally to prevent infinite loops)"
    )
