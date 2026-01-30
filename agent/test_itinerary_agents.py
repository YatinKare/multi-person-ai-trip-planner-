"""
Unit tests for itinerary generation agents and models.

Tests cover:
- Pydantic model validation
- Agent creation
- Cost validation tool
- Full pipeline integration
"""

import pytest
from tripsync.itinerary_agents import (
    create_itinerary_draft_agent,
    create_cost_sanity_agent,
    create_itinerary_polish_agent,
    validate_itinerary_costs,
    ItineraryActivity,
    ItineraryDay,
    Itinerary,
    CostValidationResult,
)


# ============================================================================
# Agent Creation Tests
# ============================================================================


def test_create_itinerary_draft_agent():
    """Test that ItineraryDraftAgent is created successfully."""
    agent = create_itinerary_draft_agent()
    assert agent is not None
    assert hasattr(agent, 'model')
    assert agent.model == "gemini-2.5-flash"


def test_create_cost_sanity_agent():
    """Test that CostSanityAgent is created with tool."""
    agent = create_cost_sanity_agent()
    assert agent is not None
    assert hasattr(agent, 'tools')
    assert len(agent.tools) == 1  # Should have validate_itinerary_costs tool


def test_create_itinerary_polish_agent():
    """Test that ItineraryPolishAgent is created successfully."""
    agent = create_itinerary_polish_agent()
    assert agent is not None
    assert hasattr(agent, 'model')
    assert agent.model == "gemini-2.5-flash"


# ============================================================================
# Pydantic Model Tests
# ============================================================================


def test_itinerary_activity_model():
    """Test ItineraryActivity model validation."""
    activity = ItineraryActivity(
        title="Visit Tokyo Tower",
        description="Iconic landmark with panoramic city views",
        neighborhood_or_area="Minato",
        estimated_cost_per_person=30,
        duration_minutes=120,
        tips=["Go at sunset", "Book tickets online"]
    )
    assert activity.title == "Visit Tokyo Tower"
    assert activity.estimated_cost_per_person == 30
    assert len(activity.tips) == 2


def test_itinerary_activity_minimal():
    """Test ItineraryActivity with minimal required fields."""
    activity = ItineraryActivity(
        title="Free Walking Tour",
        description="Explore downtown on foot",
        estimated_cost_per_person=0,
    )
    assert activity.title == "Free Walking Tour"
    assert activity.estimated_cost_per_person == 0
    assert activity.neighborhood_or_area is None
    assert activity.duration_minutes is None
    assert activity.tips == []


def test_itinerary_day_model():
    """Test ItineraryDay model validation."""
    day = ItineraryDay(
        day_index=1,
        date_iso="2025-05-15",
        morning=[
            ItineraryActivity(
                title="Hotel Breakfast",
                description="Complimentary breakfast",
                estimated_cost_per_person=0,
            )
        ],
        afternoon=[
            ItineraryActivity(
                title="Museum Visit",
                description="National Art Museum",
                estimated_cost_per_person=20,
            )
        ],
        evening=[],
    )
    assert day.day_index == 1
    assert day.date_iso == "2025-05-15"
    assert len(day.morning) == 1
    assert len(day.afternoon) == 1
    assert len(day.evening) == 0


def test_itinerary_day_empty_blocks():
    """Test ItineraryDay with empty time blocks."""
    day = ItineraryDay(
        day_index=2,
    )
    assert day.day_index == 2
    assert day.date_iso is None
    assert day.morning == []
    assert day.afternoon == []
    assert day.evening == []


def test_itinerary_model():
    """Test full Itinerary model validation."""
    itinerary = Itinerary(
        trip_id="abc-123",
        destination_name="Tokyo, Japan",
        total_estimated_cost_per_person=1200,
        assumptions=["Prices in USD", "2025 estimates"],
        days=[
            ItineraryDay(
                day_index=1,
                morning=[
                    ItineraryActivity(
                        title="Arrival",
                        description="Check into hotel",
                        estimated_cost_per_person=0,
                    )
                ],
                afternoon=[],
                evening=[
                    ItineraryActivity(
                        title="Dinner",
                        description="Local restaurant",
                        estimated_cost_per_person=30,
                    )
                ],
            )
        ],
        sources=["https://example.com/tokyo"],
    )
    assert itinerary.trip_id == "abc-123"
    assert itinerary.destination_name == "Tokyo, Japan"
    assert itinerary.total_estimated_cost_per_person == 1200
    assert len(itinerary.days) == 1
    assert len(itinerary.assumptions) == 2
    assert len(itinerary.sources) == 1


def test_itinerary_minimal():
    """Test Itinerary with minimal required fields."""
    itinerary = Itinerary(
        trip_id="xyz-789",
        destination_name="Paris, France",
        total_estimated_cost_per_person=800,
        days=[],
    )
    assert itinerary.trip_id == "xyz-789"
    assert itinerary.destination_name == "Paris, France"
    assert itinerary.total_estimated_cost_per_person == 800
    assert itinerary.days == []
    assert itinerary.assumptions == []
    assert itinerary.sources == []


def test_cost_validation_result_model():
    """Test CostValidationResult model validation."""
    result = CostValidationResult(
        is_valid=True,
        total_calculated=950,
        budget_max=1000,
        budget_exceeded=False,
        issues=[],
        suggestions=[],
    )
    assert result.is_valid is True
    assert result.total_calculated == 950
    assert result.budget_max == 1000
    assert result.budget_exceeded is False


# ============================================================================
# Cost Validation Tool Tests
# ============================================================================


def test_validate_itinerary_costs_valid():
    """Test cost validation with valid costs within budget."""
    draft = {
        "days": [
            {
                "morning": [
                    {"title": "Activity 1", "estimated_cost_per_person": 50}
                ],
                "afternoon": [
                    {"title": "Activity 2", "estimated_cost_per_person": 30}
                ],
                "evening": [
                    {"title": "Activity 3", "estimated_cost_per_person": 20}
                ],
            }
        ],
        "total_estimated_cost_per_person": 100,
    }

    result = validate_itinerary_costs(draft, budget_max=150)

    assert result["is_valid"] is True
    assert result["total_calculated"] == 100
    assert result["budget_max"] == 150
    assert result["budget_exceeded"] is False
    assert len(result["issues"]) == 0


def test_validate_itinerary_costs_budget_exceeded():
    """Test cost validation when budget is exceeded."""
    draft = {
        "days": [
            {
                "morning": [
                    {"title": "Expensive Tour", "estimated_cost_per_person": 200}
                ],
                "afternoon": [],
                "evening": [],
            }
        ],
        "total_estimated_cost_per_person": 200,
    }

    result = validate_itinerary_costs(draft, budget_max=150)

    assert result["is_valid"] is False
    assert result["total_calculated"] == 200
    assert result["budget_exceeded"] is True
    assert len(result["issues"]) > 0
    assert any("exceeded" in issue.lower() for issue in result["issues"])


def test_validate_itinerary_costs_missing_costs():
    """Test cost validation with missing cost estimates."""
    draft = {
        "days": [
            {
                "morning": [
                    {"title": "Activity 1", "estimated_cost_per_person": 50}
                ],
                "afternoon": [
                    {"title": "Activity 2"}  # Missing cost!
                ],
                "evening": [],
            }
        ],
        "total_estimated_cost_per_person": 50,
    }

    result = validate_itinerary_costs(draft, budget_max=100)

    assert result["is_valid"] is False
    assert len(result["issues"]) > 0
    assert any("missing" in issue.lower() for issue in result["issues"])


def test_validate_itinerary_costs_total_mismatch():
    """Test cost validation when claimed total doesn't match calculated."""
    draft = {
        "days": [
            {
                "morning": [
                    {"title": "Activity 1", "estimated_cost_per_person": 50}
                ],
                "afternoon": [
                    {"title": "Activity 2", "estimated_cost_per_person": 30}
                ],
                "evening": [],
            }
        ],
        "total_estimated_cost_per_person": 100,  # Should be 80!
    }

    result = validate_itinerary_costs(draft, budget_max=150)

    assert result["is_valid"] is False
    assert result["total_calculated"] == 80
    assert any("mismatch" in issue.lower() for issue in result["issues"])


def test_validate_itinerary_costs_no_budget():
    """Test cost validation when no budget specified (only check for issues)."""
    draft = {
        "days": [
            {
                "morning": [
                    {"title": "Activity", "estimated_cost_per_person": 1000}
                ],
                "afternoon": [],
                "evening": [],
            }
        ],
        "total_estimated_cost_per_person": 1000,
    }

    result = validate_itinerary_costs(draft, budget_max=None)

    # Should not fail on budget, but should flag high cost
    assert result["budget_max"] is None
    assert result["budget_exceeded"] is False
    # May have warning about high cost
    assert result["total_calculated"] == 1000


def test_validate_itinerary_costs_very_high_activity():
    """Test cost validation flags very high activity costs."""
    draft = {
        "days": [
            {
                "morning": [
                    {"title": "Private Jet Tour", "estimated_cost_per_person": 500}
                ],
                "afternoon": [],
                "evening": [],
            }
        ],
        "total_estimated_cost_per_person": 500,
    }

    result = validate_itinerary_costs(draft, budget_max=1000)

    # Should flag high cost even if within budget
    assert result["total_calculated"] == 500
    assert len(result["issues"]) > 0
    assert any("high cost" in issue.lower() for issue in result["issues"])


def test_validate_itinerary_costs_too_many_free():
    """Test cost validation flags suspiciously many free activities."""
    draft = {
        "days": [
            {
                "morning": [
                    {"title": "Free Walk", "estimated_cost_per_person": 0}
                ],
                "afternoon": [
                    {"title": "Free Museum", "estimated_cost_per_person": 0}
                ],
                "evening": [
                    {"title": "Free Park", "estimated_cost_per_person": 0}
                ],
            },
            {
                "morning": [
                    {"title": "Free Tour", "estimated_cost_per_person": 0}
                ],
                "afternoon": [
                    {"title": "Paid Lunch", "estimated_cost_per_person": 15}
                ],
                "evening": [],
            },
        ],
        "total_estimated_cost_per_person": 15,
    }

    result = validate_itinerary_costs(draft, budget_max=100)

    # Should flag that 4/5 activities are free
    assert result["total_calculated"] == 15
    assert any("free activities" in issue.lower() for issue in result["issues"])


def test_validate_itinerary_costs_empty_itinerary():
    """Test cost validation with empty itinerary."""
    draft = {
        "days": [],
        "total_estimated_cost_per_person": 0,
    }

    result = validate_itinerary_costs(draft, budget_max=1000)

    assert result["is_valid"] is True
    assert result["total_calculated"] == 0


def test_validate_itinerary_costs_multiple_days():
    """Test cost validation across multiple days."""
    draft = {
        "days": [
            {
                "morning": [
                    {"title": "Day 1 Morning", "estimated_cost_per_person": 30}
                ],
                "afternoon": [
                    {"title": "Day 1 Afternoon", "estimated_cost_per_person": 40}
                ],
                "evening": [
                    {"title": "Day 1 Evening", "estimated_cost_per_person": 50}
                ],
            },
            {
                "morning": [
                    {"title": "Day 2 Morning", "estimated_cost_per_person": 20}
                ],
                "afternoon": [
                    {"title": "Day 2 Afternoon", "estimated_cost_per_person": 35}
                ],
                "evening": [
                    {"title": "Day 2 Evening", "estimated_cost_per_person": 45}
                ],
            },
        ],
        "total_estimated_cost_per_person": 220,
    }

    result = validate_itinerary_costs(draft, budget_max=250)

    assert result["is_valid"] is True
    assert result["total_calculated"] == 220
    assert result["budget_exceeded"] is False


# ============================================================================
# Integration Tests
# ============================================================================


def test_full_itinerary_pipeline_structure():
    """Test that all three agents can be created for a complete pipeline."""
    draft_agent = create_itinerary_draft_agent()
    cost_agent = create_cost_sanity_agent()
    polish_agent = create_itinerary_polish_agent()

    assert draft_agent is not None
    assert cost_agent is not None
    assert polish_agent is not None

    # Verify cost agent has the validation tool
    assert hasattr(cost_agent, 'tools')
    assert len(cost_agent.tools) == 1


def test_itinerary_models_work_together():
    """Test that all itinerary models work together in a complete structure."""
    # Create activities
    activities = [
        ItineraryActivity(
            title="Morning Activity",
            description="Start the day right",
            estimated_cost_per_person=25,
        ),
        ItineraryActivity(
            title="Afternoon Activity",
            description="Midday fun",
            estimated_cost_per_person=40,
        ),
    ]

    # Create days
    day1 = ItineraryDay(
        day_index=1,
        date_iso="2025-05-15",
        morning=[activities[0]],
        afternoon=[activities[1]],
        evening=[],
    )

    day2 = ItineraryDay(
        day_index=2,
        date_iso="2025-05-16",
        morning=[],
        afternoon=[activities[0]],  # Reuse activity
        evening=[],
    )

    # Create full itinerary
    itinerary = Itinerary(
        trip_id="test-123",
        destination_name="Test City",
        total_estimated_cost_per_person=90,
        days=[day1, day2],
        assumptions=["Test assumptions"],
        sources=["https://test.com"],
    )

    assert len(itinerary.days) == 2
    assert itinerary.total_estimated_cost_per_person == 90

    # Verify we can convert to dict for validation
    itinerary_dict = itinerary.model_dump()
    result = validate_itinerary_costs(itinerary_dict, budget_max=100)

    assert result["is_valid"] is True
    assert result["total_calculated"] == 90
