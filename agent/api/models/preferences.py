"""Pydantic models for preferences and aggregation."""

from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field


class DatePreferences(BaseModel):
    """User's date preferences for a trip."""

    earliest_start: date = Field(..., description="Earliest possible start date")
    latest_end: date = Field(..., description="Latest possible end date")
    ideal_length: str = Field(
        ...,
        description="Ideal trip length: '2-3 days', '4-5 days', '1 week', '1+ week', 'flexible'"
    )
    flexible: bool = Field(default=False, description="Whether dates are flexible")


class BudgetPreferences(BaseModel):
    """User's budget preferences."""

    min_budget: float = Field(..., ge=0, description="Minimum budget per person in USD")
    max_budget: float = Field(..., ge=0, description="Maximum budget per person in USD")
    includes: List[str] = Field(
        default_factory=list,
        description="What's included: flights, accommodation, food, activities"
    )
    flexibility: str = Field(
        ...,
        description="Budget flexibility: 'hard limit', 'prefer under', 'no limit'"
    )


class DestinationPreferences(BaseModel):
    """User's destination preferences."""

    vibes: List[str] = Field(
        default_factory=list,
        description="Selected vibes: Beach, City, Nature, Adventure, Relaxation, Nightlife, Culture, Food-focused, Road trip"
    )
    specific_places: Optional[str] = Field(None, description="Specific places in mind")
    places_to_avoid: Optional[str] = Field(None, description="Places to avoid")
    domestic_international: str = Field(
        ...,
        description="Preference: 'domestic', 'international', 'either'"
    )


class ConstraintsPreferences(BaseModel):
    """User's constraints and deal-breakers."""

    dietary_restrictions: List[str] = Field(
        default_factory=list,
        description="Dietary restrictions: vegetarian, vegan, gluten-free, halal, kosher, allergies, other"
    )
    accessibility_needs: List[str] = Field(
        default_factory=list,
        description="Accessibility needs"
    )
    hard_nos: Optional[str] = Field(None, description="Hard no's and deal-breakers")


class Conflict(BaseModel):
    """Represents a conflict in group preferences."""

    type: str = Field(..., description="Type of conflict: date_overlap, budget_mismatch, no_common_vibes")
    description: str = Field(..., description="Human-readable description of the conflict")
    affected_members: List[str] = Field(
        default_factory=list,
        description="User IDs of affected members"
    )


class AggregatedPreferences(BaseModel):
    """Aggregated preferences for the entire trip group."""

    # Date aggregation
    common_start_earliest: Optional[date] = Field(None, description="Earliest common start date")
    common_end_latest: Optional[date] = Field(None, description="Latest common end date")
    date_overlap_days: Optional[int] = Field(None, description="Number of overlapping days")

    # Budget aggregation
    budget_min: float = Field(..., description="Minimum budget across all members")
    budget_max: float = Field(..., description="Maximum budget across all members")
    budget_average: float = Field(..., description="Average budget across all members")

    # Destination aggregation
    common_vibes: List[str] = Field(
        default_factory=list,
        description="Vibes selected by all or most members"
    )
    all_vibes: List[str] = Field(
        default_factory=list,
        description="All vibes mentioned by any member"
    )
    domestic_international_preference: str = Field(
        ...,
        description="Group consensus: 'domestic', 'international', 'either', 'mixed'"
    )

    # Constraints aggregation
    all_dietary_restrictions: List[str] = Field(
        default_factory=list,
        description="All dietary restrictions from all members"
    )
    all_accessibility_needs: List[str] = Field(
        default_factory=list,
        description="All accessibility needs from all members"
    )
    all_hard_nos: List[str] = Field(
        default_factory=list,
        description="All deal-breakers from all members"
    )

    # Conflicts
    conflicts: List[Conflict] = Field(
        default_factory=list,
        description="List of detected conflicts"
    )

    # Metadata
    total_members: int = Field(..., description="Total number of trip members")
    responded_members: int = Field(..., description="Number of members who submitted preferences")
    response_rate: float = Field(..., description="Percentage of members who responded (0-100)")
