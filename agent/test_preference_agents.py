"""
Unit Tests for Preference & Intelligence Agents

Tests the agent creation functions and aggregation logic.
"""

import pytest

from tripsync.preference_agents import (
    create_preference_normalizer_agent,
    aggregate_preferences,
    create_conflict_detector_agent,
    NormalizedPreference,
    AggregatedGroupProfile,
    ConflictReport,
)


# ============================================================================
# Test Agent Creation
# ============================================================================


def test_create_preference_normalizer_agent():
    """Test that PreferenceNormalizerAgent is created correctly."""
    agent = create_preference_normalizer_agent()

    assert agent is not None
    assert agent.model == "gemini-2.5-flash"
    assert agent.instruction is not None
    assert "PreferenceNormalizerAgent" in agent.instruction
    assert "NormalizedPreference" in agent.instruction
    assert len(agent.tools) == 0  # No tools for this agent


def test_create_conflict_detector_agent():
    """Test that ConflictDetectorAgent is created correctly."""
    agent = create_conflict_detector_agent()

    assert agent is not None
    assert agent.model == "gemini-2.5-flash"
    assert agent.instruction is not None
    assert "ConflictDetectorAgent" in agent.instruction
    assert "ConflictReport" in agent.instruction
    assert len(agent.tools) == 0  # No tools for this agent


# ============================================================================
# Test Pydantic Models
# ============================================================================


def test_normalized_preference_model():
    """Test NormalizedPreference Pydantic model."""
    pref = NormalizedPreference(
        user_id="abc123",
        dates={"earliest_start": "2025-06-01", "confidence": 0.9},
        budget={"max_budget": 1000, "confidence": 0.8},
        destination_prefs={"vibes": ["Beach"], "confidence": 0.7},
        constraints={"dietary_restrictions": ["vegetarian"]},
        notes="Test notes",
        confidence_score=0.85
    )

    assert pref.user_id == "abc123"
    assert pref.dates["confidence"] == 0.9
    assert pref.budget["confidence"] == 0.8
    assert pref.destination_prefs["confidence"] == 0.7
    assert pref.confidence_score == 0.85


def test_normalized_preference_confidence_validation():
    """Test that confidence_score is validated (0-1 range)."""
    # Valid confidence score
    pref = NormalizedPreference(
        user_id="abc123",
        dates={},
        budget={},
        destination_prefs={},
        constraints={},
        confidence_score=0.5
    )
    assert pref.confidence_score == 0.5

    # Invalid confidence score (> 1)
    with pytest.raises(ValueError):
        NormalizedPreference(
            user_id="abc123",
            dates={},
            budget={},
            destination_prefs={},
            constraints={},
            confidence_score=1.5
        )

    # Invalid confidence score (< 0)
    with pytest.raises(ValueError):
        NormalizedPreference(
            user_id="abc123",
            dates={},
            budget={},
            destination_prefs={},
            constraints={},
            confidence_score=-0.5
        )


def test_aggregated_group_profile_model():
    """Test AggregatedGroupProfile Pydantic model."""
    profile = AggregatedGroupProfile(
        date_overlap={"has_overlap": True, "overlap_days": 7},
        budget_range={"min_budget": 500, "max_budget": 1500},
        vibes={"common_vibes": ["Beach"], "all_vibes": ["Beach", "City"]},
        constraints={"dietary_restrictions": ["vegetarian"]},
        member_count=3
    )

    assert profile.date_overlap["has_overlap"] is True
    assert profile.budget_range["min_budget"] == 500
    assert profile.vibes["common_vibes"] == ["Beach"]
    assert profile.member_count == 3


def test_conflict_report_model():
    """Test ConflictReport Pydantic model."""
    report = ConflictReport(
        has_conflicts=True,
        conflicts=[
            {
                "type": "date",
                "severity": "high",
                "description": "No date overlap",
                "affected_members": ["abc123", "def456"],
                "resolutions": ["Ask members to expand date ranges"]
            }
        ],
        overall_severity="high",
        can_proceed=False,
        summary="Critical date conflict detected"
    )

    assert report.has_conflicts is True
    assert len(report.conflicts) == 1
    assert report.conflicts[0]["type"] == "date"
    assert report.overall_severity == "high"
    assert report.can_proceed is False


# ============================================================================
# Test aggregate_preferences Function (AggregationAgent)
# ============================================================================


def test_aggregate_preferences_with_valid_data():
    """Test preference aggregation with valid normalized preferences."""
    normalized_preferences = [
        {
            "dates": {
                "earliest_start": "2025-06-01",
                "latest_end": "2025-06-15"
            },
            "budget": {
                "min_budget": 500,
                "max_budget": 1500
            },
            "destination_prefs": {
                "vibes": ["Beach", "Relaxation"]
            },
            "constraints": {
                "dietary_restrictions": ["vegetarian"],
                "hard_nos": "No camping"
            }
        },
        {
            "dates": {
                "earliest_start": "2025-06-05",
                "latest_end": "2025-06-20"
            },
            "budget": {
                "min_budget": 800,
                "max_budget": 2000
            },
            "destination_prefs": {
                "vibes": ["Beach", "Food-focused"]
            },
            "constraints": {
                "dietary_restrictions": ["vegan"]
            }
        }
    ]

    result = aggregate_preferences(normalized_preferences)

    # Check type
    assert isinstance(result, AggregatedGroupProfile)

    # Check date overlap
    assert result.date_overlap["has_overlap"] is True
    assert result.date_overlap["overlap_days"] == 11

    # Check budget range
    assert result.budget_range["has_feasible_range"] is True
    assert result.budget_range["min_budget"] == 800
    assert result.budget_range["max_budget"] == 1500

    # Check vibes
    assert result.vibes["has_common_vibes"] is True
    assert "Beach" in result.vibes["common_vibes"]

    # Check constraints
    assert "vegetarian" in result.constraints["dietary_restrictions"]
    assert "vegan" in result.constraints["dietary_restrictions"]

    # Check member count
    assert result.member_count == 2


def test_aggregate_preferences_with_conflicts():
    """Test preference aggregation with conflicting preferences."""
    normalized_preferences = [
        {
            "dates": {
                "earliest_start": "2025-06-01",
                "latest_end": "2025-06-10"
            },
            "budget": {
                "min_budget": 500,
                "max_budget": 800
            },
            "destination_prefs": {
                "vibes": ["Beach"]
            },
            "constraints": {}
        },
        {
            "dates": {
                "earliest_start": "2025-06-15",
                "latest_end": "2025-06-25"
            },
            "budget": {
                "min_budget": 1000,
                "max_budget": 1500
            },
            "destination_prefs": {
                "vibes": ["City"]
            },
            "constraints": {}
        }
    ]

    result = aggregate_preferences(normalized_preferences)

    # Check conflicts are detected in aggregation
    assert result.date_overlap["has_overlap"] is False  # No date overlap
    assert result.budget_range["has_feasible_range"] is False  # Budget conflict
    assert result.vibes["has_common_vibes"] is False  # No common vibes


def test_aggregate_preferences_empty_list():
    """Test preference aggregation with empty preference list."""
    result = aggregate_preferences([])

    assert isinstance(result, AggregatedGroupProfile)
    assert result.member_count == 0
    assert result.date_overlap["has_overlap"] is False
    assert result.budget_range["has_feasible_range"] is False
    assert result.vibes["has_common_vibes"] is False


def test_aggregate_preferences_single_member():
    """Test preference aggregation with single member."""
    normalized_preferences = [
        {
            "dates": {
                "earliest_start": "2025-06-01",
                "latest_end": "2025-06-15"
            },
            "budget": {
                "min_budget": 500,
                "max_budget": 1500
            },
            "destination_prefs": {
                "vibes": ["Beach", "Relaxation"]
            },
            "constraints": {}
        }
    ]

    result = aggregate_preferences(normalized_preferences)

    assert result.member_count == 1
    assert result.date_overlap["has_overlap"] is True
    assert result.budget_range["has_feasible_range"] is True
    assert result.vibes["has_common_vibes"] is True
    assert len(result.vibes["common_vibes"]) == 2


def test_aggregate_preferences_all_flexible():
    """Test preference aggregation when all members are flexible."""
    normalized_preferences = [
        {
            "dates": {},
            "budget": {},
            "destination_prefs": {"vibes": []},
            "constraints": {}
        },
        {
            "dates": {},
            "budget": {},
            "destination_prefs": {"vibes": []},
            "constraints": {}
        }
    ]

    result = aggregate_preferences(normalized_preferences)

    assert result.member_count == 2
    # Empty preferences should result in no overlap/feasible data
    assert result.date_overlap["has_overlap"] is False
    assert result.budget_range["has_feasible_range"] is False
    assert result.vibes["has_common_vibes"] is False


# ============================================================================
# Integration Test: Full Pipeline
# ============================================================================


def test_full_preference_pipeline():
    """Test the full preference processing pipeline."""
    # Step 1: Create agents
    normalizer = create_preference_normalizer_agent()
    conflict_detector = create_conflict_detector_agent()

    assert normalizer is not None
    assert conflict_detector is not None

    # Step 2: Simulate normalized preferences (would come from normalizer in real usage)
    normalized_preferences = [
        {
            "dates": {
                "earliest_start": "2025-06-01",
                "latest_end": "2025-06-15"
            },
            "budget": {
                "min_budget": 500,
                "max_budget": 1500
            },
            "destination_prefs": {
                "vibes": ["Beach", "Relaxation"]
            },
            "constraints": {
                "dietary_restrictions": ["vegetarian"]
            }
        },
        {
            "dates": {
                "earliest_start": "2025-06-05",
                "latest_end": "2025-06-20"
            },
            "budget": {
                "min_budget": 800,
                "max_budget": 2000
            },
            "destination_prefs": {
                "vibes": ["Beach", "Food-focused"]
            },
            "constraints": {
                "dietary_restrictions": ["vegan"]
            }
        }
    ]

    # Step 3: Aggregate preferences
    aggregated = aggregate_preferences(normalized_preferences)

    assert aggregated.member_count == 2
    assert aggregated.date_overlap["has_overlap"] is True
    assert aggregated.budget_range["has_feasible_range"] is True
    assert aggregated.vibes["has_common_vibes"] is True

    # Step 4: Conflict detector would analyze aggregated profile
    # (In real usage, this would be called via ADK with session state)
    # Here we just verify the agent is ready to process


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
