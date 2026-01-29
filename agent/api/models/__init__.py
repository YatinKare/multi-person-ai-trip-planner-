"""Pydantic models for request/response validation."""

from .preferences import (
    DatePreferences,
    BudgetPreferences,
    DestinationPreferences,
    ConstraintsPreferences,
    AggregatedPreferences,
    Conflict,
)
from .recommendations import (
    SampleHighlight,
    DestinationRecommendation,
    GenerateRecommendationsRequest,
    GenerateRecommendationsResponse,
)
from .itinerary import (
    Activity,
    DayItinerary,
    GenerateItineraryRequest,
    GenerateItineraryResponse,
    RegenerateItineraryRequest,
)

__all__ = [
    # Preferences
    "DatePreferences",
    "BudgetPreferences",
    "DestinationPreferences",
    "ConstraintsPreferences",
    "AggregatedPreferences",
    "Conflict",
    # Recommendations
    "SampleHighlight",
    "DestinationRecommendation",
    "GenerateRecommendationsRequest",
    "GenerateRecommendationsResponse",
    # Itinerary
    "Activity",
    "DayItinerary",
    "GenerateItineraryRequest",
    "GenerateItineraryResponse",
    "RegenerateItineraryRequest",
]
