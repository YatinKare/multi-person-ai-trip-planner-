"""Unit tests for Pydantic models."""

import pytest
from datetime import date
from uuid import uuid4
from pydantic import ValidationError

from api.models import (
    DatePreferences,
    BudgetPreferences,
    DestinationPreferences,
    ConstraintsPreferences,
    AggregatedPreferences,
    Conflict,
    SampleHighlight,
    DestinationRecommendation,
    GenerateRecommendationsRequest,
    GenerateRecommendationsResponse,
    Activity,
    DayItinerary,
    GenerateItineraryRequest,
    GenerateItineraryResponse,
    RegenerateItineraryRequest,
)


class TestPreferencesModels:
    """Tests for preference-related models."""

    def test_date_preferences_valid(self):
        """Test valid DatePreferences."""
        prefs = DatePreferences(
            earliest_start=date(2026, 5, 1),
            latest_end=date(2026, 5, 10),
            ideal_length="4-5 days",
            flexible=True
        )
        assert prefs.earliest_start == date(2026, 5, 1)
        assert prefs.flexible is True

    def test_budget_preferences_valid(self):
        """Test valid BudgetPreferences."""
        prefs = BudgetPreferences(
            min_budget=500.0,
            max_budget=1500.0,
            includes=["flights", "accommodation"],
            flexibility="prefer under"
        )
        assert prefs.min_budget == 500.0
        assert "flights" in prefs.includes

    def test_budget_preferences_negative_fails(self):
        """Test that negative budgets fail validation."""
        with pytest.raises(ValidationError):
            BudgetPreferences(
                min_budget=-100.0,
                max_budget=1500.0,
                includes=[],
                flexibility="hard limit"
            )

    def test_destination_preferences_valid(self):
        """Test valid DestinationPreferences."""
        prefs = DestinationPreferences(
            vibes=["Beach", "Relaxation", "Food-focused"],
            specific_places="Hawaii or Mexico",
            places_to_avoid="Las Vegas",
            domestic_international="either"
        )
        assert len(prefs.vibes) == 3
        assert prefs.specific_places == "Hawaii or Mexico"

    def test_constraints_preferences_valid(self):
        """Test valid ConstraintsPreferences."""
        prefs = ConstraintsPreferences(
            dietary_restrictions=["vegetarian", "gluten-free"],
            accessibility_needs=["wheelchair accessible"],
            hard_nos="No camping, no red-eye flights"
        )
        assert "vegetarian" in prefs.dietary_restrictions

    def test_aggregated_preferences_valid(self):
        """Test valid AggregatedPreferences."""
        conflict = Conflict(
            type="budget_mismatch",
            description="Budget ranges don't overlap",
            affected_members=["user1", "user2"]
        )

        agg = AggregatedPreferences(
            common_start_earliest=date(2026, 5, 1),
            common_end_latest=date(2026, 5, 10),
            date_overlap_days=9,
            budget_min=500.0,
            budget_max=2000.0,
            budget_average=1250.0,
            common_vibes=["Beach", "Relaxation"],
            all_vibes=["Beach", "Relaxation", "City", "Adventure"],
            domestic_international_preference="either",
            all_dietary_restrictions=["vegetarian", "vegan"],
            all_accessibility_needs=["wheelchair accessible"],
            all_hard_nos=["No camping"],
            conflicts=[conflict],
            total_members=5,
            responded_members=4,
            response_rate=80.0
        )
        assert agg.total_members == 5
        assert len(agg.conflicts) == 1


class TestRecommendationsModels:
    """Tests for recommendation-related models."""

    def test_sample_highlight_valid(self):
        """Test valid SampleHighlight."""
        highlight = SampleHighlight(
            day=1,
            title="Beach visit",
            description="Relax at the beautiful beach"
        )
        assert highlight.day == 1

    def test_destination_recommendation_valid(self):
        """Test valid DestinationRecommendation."""
        rec = DestinationRecommendation(
            name="Tulum",
            region="Mexico",
            reasoning="Perfect beach destination with cultural sites",
            cost_estimate_min=800.0,
            cost_estimate_max=1200.0,
            sample_highlights=[
                SampleHighlight(day=1, title="Beach day", description="Relax at the beach"),
                SampleHighlight(day=2, title="Ruins tour", description="Visit Mayan ruins")
            ],
            tradeoffs="Requires international travel"
        )
        assert rec.name == "Tulum"
        assert len(rec.sample_highlights) == 2

    def test_destination_recommendation_negative_cost_fails(self):
        """Test that negative costs fail validation."""
        with pytest.raises(ValidationError):
            DestinationRecommendation(
                name="Test",
                region="Test Region",
                reasoning="Test reasoning",
                cost_estimate_min=-100.0,
                cost_estimate_max=1000.0,
                sample_highlights=[
                    SampleHighlight(day=1, title="Test", description="Test")
                ]
            )

    def test_generate_recommendations_request_valid(self):
        """Test valid GenerateRecommendationsRequest."""
        trip_id = uuid4()
        req = GenerateRecommendationsRequest(trip_id=trip_id)
        assert req.trip_id == trip_id

    def test_generate_recommendations_response_valid(self):
        """Test valid GenerateRecommendationsResponse."""
        trip_id = uuid4()
        destinations = [
            DestinationRecommendation(
                name=f"Destination {i}",
                region="Region",
                reasoning="Test reasoning",
                cost_estimate_min=500.0,
                cost_estimate_max=1000.0,
                sample_highlights=[
                    SampleHighlight(day=1, title="Day 1", description="Activity")
                ]
            )
            for i in range(3)
        ]

        resp = GenerateRecommendationsResponse(
            trip_id=trip_id,
            destinations=destinations,
            generated_at="2026-01-29T12:00:00Z"
        )
        assert len(resp.destinations) == 3

    def test_generate_recommendations_response_too_few_destinations_fails(self):
        """Test that < 3 destinations fails validation."""
        trip_id = uuid4()
        destinations = [
            DestinationRecommendation(
                name="Dest 1",
                region="Region",
                reasoning="Test",
                cost_estimate_min=500.0,
                cost_estimate_max=1000.0,
                sample_highlights=[
                    SampleHighlight(day=1, title="Day 1", description="Activity")
                ]
            )
        ]

        with pytest.raises(ValidationError):
            GenerateRecommendationsResponse(
                trip_id=trip_id,
                destinations=destinations,
                generated_at="2026-01-29T12:00:00Z"
            )


class TestItineraryModels:
    """Tests for itinerary-related models."""

    def test_activity_valid(self):
        """Test valid Activity."""
        activity = Activity(
            name="Breakfast at Cafe",
            description="Enjoy local breakfast",
            time_slot="morning",
            estimated_cost=15.0,
            location="123 Main St",
            duration_hours=1.5,
            tips="Try the pancakes"
        )
        assert activity.name == "Breakfast at Cafe"
        assert activity.estimated_cost == 15.0

    def test_activity_negative_cost_fails(self):
        """Test that negative cost fails validation."""
        with pytest.raises(ValidationError):
            Activity(
                name="Test",
                description="Test",
                time_slot="morning",
                estimated_cost=-10.0,
                location="Test",
                duration_hours=1.0
            )

    def test_activity_zero_duration_fails(self):
        """Test that zero duration fails validation."""
        with pytest.raises(ValidationError):
            Activity(
                name="Test",
                description="Test",
                time_slot="morning",
                estimated_cost=10.0,
                location="Test",
                duration_hours=0.0
            )

    def test_day_itinerary_valid(self):
        """Test valid DayItinerary."""
        activities = [
            Activity(
                name="Activity 1",
                description="Description",
                time_slot="morning",
                estimated_cost=20.0,
                location="Location",
                duration_hours=2.0
            ),
            Activity(
                name="Activity 2",
                description="Description",
                time_slot="afternoon",
                estimated_cost=30.0,
                location="Location",
                duration_hours=3.0
            )
        ]

        day = DayItinerary(
            day_number=1,
            date="2026-05-01",
            title="Arrival Day",
            activities=activities,
            total_cost=50.0
        )
        assert day.day_number == 1
        assert len(day.activities) == 2
        assert day.total_cost == 50.0

    def test_generate_itinerary_request_valid(self):
        """Test valid GenerateItineraryRequest."""
        trip_id = uuid4()
        req = GenerateItineraryRequest(
            trip_id=trip_id,
            destination_name="Tulum"
        )
        assert req.trip_id == trip_id
        assert req.destination_name == "Tulum"

    def test_generate_itinerary_response_valid(self):
        """Test valid GenerateItineraryResponse."""
        trip_id = uuid4()
        days = [
            DayItinerary(
                day_number=i,
                activities=[
                    Activity(
                        name="Activity",
                        description="Description",
                        time_slot="morning",
                        estimated_cost=20.0,
                        location="Location",
                        duration_hours=2.0
                    )
                ],
                total_cost=20.0
            )
            for i in range(1, 4)
        ]

        resp = GenerateItineraryResponse(
            trip_id=trip_id,
            destination_name="Tulum",
            days=days,
            total_cost=60.0,
            trip_length_days=3,
            generated_at="2026-01-29T12:00:00Z"
        )
        assert len(resp.days) == 3
        assert resp.total_cost == 60.0

    def test_regenerate_itinerary_request_valid(self):
        """Test valid RegenerateItineraryRequest."""
        trip_id = uuid4()
        req = RegenerateItineraryRequest(
            trip_id=trip_id,
            feedback="Make it more budget-friendly",
            regeneration_count=1
        )
        assert req.feedback == "Make it more budget-friendly"
        assert req.regeneration_count == 1

    def test_regenerate_itinerary_request_empty_feedback_fails(self):
        """Test that empty feedback fails validation."""
        trip_id = uuid4()
        with pytest.raises(ValidationError):
            RegenerateItineraryRequest(
                trip_id=trip_id,
                feedback=""
            )

    def test_regenerate_itinerary_request_too_long_feedback_fails(self):
        """Test that feedback > 1000 chars fails validation."""
        trip_id = uuid4()
        with pytest.raises(ValidationError):
            RegenerateItineraryRequest(
                trip_id=trip_id,
                feedback="x" * 1001
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
