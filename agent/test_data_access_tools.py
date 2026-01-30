"""
Unit tests for data access tools.

Tests the TripSync data access layer that provides agents with
database operations.
"""
import pytest
from tripsync.data_access_tools import (
    load_trip_context,
    load_member_preferences,
    load_existing_recommendations,
    load_existing_itinerary,
    store_recommendations,
    store_itinerary,
    store_progress
)


class TestDataAccessTools:
    """Tests for data access tool functions."""

    def test_load_trip_context_with_invalid_id(self):
        """Test loading trip context with non-existent ID returns error."""
        result = load_trip_context("00000000-0000-0000-0000-000000000000")
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_load_member_preferences_with_invalid_id(self):
        """Test loading preferences with non-existent trip ID returns empty list."""
        result = load_member_preferences("00000000-0000-0000-0000-000000000000")
        assert isinstance(result, list)
        # Should return empty list for non-existent trip (no error in preferences)
        assert len(result) == 0

    def test_load_existing_recommendations_with_invalid_id(self):
        """Test loading recommendations with non-existent trip ID returns None."""
        result = load_existing_recommendations("00000000-0000-0000-0000-000000000000")
        assert result is None

    def test_load_existing_itinerary_with_invalid_id(self):
        """Test loading itinerary with non-existent trip ID returns None."""
        result = load_existing_itinerary("00000000-0000-0000-0000-000000000000")
        assert result is None

    def test_store_recommendations_structure(self):
        """Test store_recommendations returns correct structure."""
        # With invalid trip_id, should still return proper structure with error
        result = store_recommendations(
            "00000000-0000-0000-0000-000000000000",
            {
                "options": [],
                "generated_by": "test-user-id",
                "group_summary": "Test summary",
                "conflicts": []
            }
        )
        assert "success" in result
        # Will fail to insert but should return structured response
        assert isinstance(result["success"], bool)

    def test_store_itinerary_structure(self):
        """Test store_itinerary returns correct structure."""
        # With invalid trip_id, should still return proper structure with error
        result = store_itinerary(
            "00000000-0000-0000-0000-000000000000",
            {
                "destination_name": "Test Destination",
                "days": [],
                "total_cost": 1000,
                "generated_by": "test-user-id"
            }
        )
        assert "success" in result
        assert isinstance(result["success"], bool)

    def test_store_progress(self):
        """Test store_progress returns success."""
        result = store_progress(
            "test-trip-id",
            "Test progress message",
            "test_stage"
        )
        assert result["success"] is True
        assert result["message"] == "Test progress message"
        assert result["stage"] == "test_stage"

    def test_load_trip_context_structure(self):
        """Test load_trip_context returns expected keys (on error)."""
        result = load_trip_context("00000000-0000-0000-0000-000000000000")
        assert isinstance(result, dict)
        assert "error" in result  # Should have error for non-existent trip

    def test_store_recommendations_with_empty_payload(self):
        """Test store_recommendations handles empty payload."""
        result = store_recommendations(
            "00000000-0000-0000-0000-000000000000",
            {}
        )
        assert "success" in result
        assert isinstance(result["success"], bool)

    def test_store_itinerary_with_minimal_payload(self):
        """Test store_itinerary with minimal required fields."""
        result = store_itinerary(
            "00000000-0000-0000-0000-000000000000",
            {
                "destination_name": "Test",
                "days": [],
                "total_cost": 0
            }
        )
        assert "success" in result
        assert isinstance(result["success"], bool)
