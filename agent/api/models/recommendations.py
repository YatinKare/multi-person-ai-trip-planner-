"""Pydantic models for destination recommendations."""

from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID


class SampleHighlight(BaseModel):
    """A sample activity/highlight for a destination."""

    day: int = Field(..., description="Day number (1 or 2 for 2-day sample)")
    title: str = Field(..., description="Activity or highlight title")
    description: str = Field(..., description="Brief description of the activity")


class DestinationRecommendation(BaseModel):
    """A single destination recommendation from AI."""

    name: str = Field(..., description="Destination name (city, region, or area)")
    region: str = Field(..., description="Broader geographic region or country")
    reasoning: str = Field(..., description="Why this destination fits the group (AI reasoning)")
    cost_estimate_min: float = Field(..., ge=0, description="Minimum estimated cost per person")
    cost_estimate_max: float = Field(..., ge=0, description="Maximum estimated cost per person")
    sample_highlights: List[SampleHighlight] = Field(
        ...,
        description="2-day sample itinerary highlights",
        min_length=1
    )
    tradeoffs: Optional[str] = Field(
        None,
        description="Any tradeoffs or notes (e.g., 'slightly over budget', 'requires international travel')"
    )
    image_url: Optional[str] = Field(None, description="Optional image URL for the destination")


class GenerateRecommendationsRequest(BaseModel):
    """Request to generate destination recommendations."""

    trip_id: UUID = Field(..., description="Trip ID to generate recommendations for")
    # Aggregated preferences will be fetched from the database based on trip_id
    # No need to include them in the request


class GenerateRecommendationsResponse(BaseModel):
    """Response containing destination recommendations."""

    trip_id: UUID = Field(..., description="Trip ID these recommendations are for")
    destinations: List[DestinationRecommendation] = Field(
        ...,
        description="List of 3-5 destination recommendations",
        min_length=3,
        max_length=5
    )
    generated_at: str = Field(..., description="Timestamp when recommendations were generated (ISO 8601)")
    aggregated_preferences_summary: Optional[str] = Field(
        None,
        description="Human-readable summary of aggregated preferences used"
    )
