"""
Unit Tests for Computation Tools

Tests the deterministic computation functions used by preference agents.
"""

import pytest
from datetime import datetime

from tripsync.computation_tools import (
    compute_date_overlap,
    compute_budget_range,
    intersect_vibes,
    extract_hard_constraints,
)


# ============================================================================
# Test compute_date_overlap
# ============================================================================


def test_compute_date_overlap_with_valid_overlap():
    """Test date overlap computation with valid overlapping ranges."""
    preferences = [
        {
            "dates": {
                "earliest_start": "2025-06-01",
                "latest_end": "2025-06-15"
            }
        },
        {
            "dates": {
                "earliest_start": "2025-06-05",
                "latest_end": "2025-06-20"
            }
        },
        {
            "dates": {
                "earliest_start": "2025-06-03",
                "latest_end": "2025-06-12"
            }
        }
    ]

    result = compute_date_overlap(preferences)

    assert result["has_overlap"] is True
    assert result["overlap_start"] == "2025-06-05T00:00:00"
    assert result["overlap_end"] == "2025-06-12T00:00:00"
    assert result["overlap_days"] == 8
    assert result["members_with_dates"] == 3


def test_compute_date_overlap_no_overlap():
    """Test date overlap with non-overlapping ranges."""
    preferences = [
        {
            "dates": {
                "earliest_start": "2025-06-01",
                "latest_end": "2025-06-10"
            }
        },
        {
            "dates": {
                "earliest_start": "2025-06-15",
                "latest_end": "2025-06-25"
            }
        }
    ]

    result = compute_date_overlap(preferences)

    assert result["has_overlap"] is False
    assert result["overlap_start"] is None
    assert result["overlap_end"] is None
    assert result["overlap_days"] == 0
    assert result["members_with_dates"] == 2


def test_compute_date_overlap_empty_preferences():
    """Test date overlap with no date preferences."""
    preferences = [
        {"dates": {}},
        {"destination_prefs": {"vibes": ["Beach"]}}
    ]

    result = compute_date_overlap(preferences)

    assert result["has_overlap"] is False
    assert result["overlap_start"] is None
    assert result["overlap_end"] is None
    assert result["overlap_days"] == 0
    assert result["members_with_dates"] == 0


def test_compute_date_overlap_single_member():
    """Test date overlap with single member."""
    preferences = [
        {
            "dates": {
                "earliest_start": "2025-06-01",
                "latest_end": "2025-06-15"
            }
        }
    ]

    result = compute_date_overlap(preferences)

    assert result["has_overlap"] is True
    assert result["overlap_start"] == "2025-06-01T00:00:00"
    assert result["overlap_end"] == "2025-06-15T00:00:00"
    assert result["overlap_days"] == 15
    assert result["members_with_dates"] == 1


# ============================================================================
# Test compute_budget_range
# ============================================================================


def test_compute_budget_range_with_valid_ranges():
    """Test budget range computation with valid overlapping ranges."""
    preferences = [
        {
            "budget": {
                "min_budget": 500,
                "max_budget": 1500
            }
        },
        {
            "budget": {
                "min_budget": 800,
                "max_budget": 2000
            }
        },
        {
            "budget": {
                "min_budget": 600,
                "max_budget": 1200
            }
        }
    ]

    result = compute_budget_range(preferences)

    assert result["min_budget"] == 800  # max of mins
    assert result["max_budget"] == 1200  # min of maxs
    assert result["has_feasible_range"] is True
    # Average: ((500+1500)/2 + (800+2000)/2 + (600+1200)/2) / 3 = (1000 + 1400 + 900) / 3 = 1100
    assert result["average_budget"] == 1100.0
    assert result["members_with_budgets"] == 3


def test_compute_budget_range_no_overlap():
    """Test budget range with non-overlapping ranges."""
    preferences = [
        {
            "budget": {
                "min_budget": 500,
                "max_budget": 800
            }
        },
        {
            "budget": {
                "min_budget": 1000,
                "max_budget": 1500
            }
        }
    ]

    result = compute_budget_range(preferences)

    assert result["min_budget"] == 1000  # max of mins
    assert result["max_budget"] == 800  # min of maxs
    assert result["has_feasible_range"] is False  # 1000 > 800
    assert result["members_with_budgets"] == 2


def test_compute_budget_range_empty_preferences():
    """Test budget range with no budget preferences."""
    preferences = [
        {"dates": {"earliest_start": "2025-06-01"}},
        {"destination_prefs": {"vibes": ["Beach"]}}
    ]

    result = compute_budget_range(preferences)

    assert result["min_budget"] == 0
    assert result["max_budget"] == 0
    assert result["has_feasible_range"] is False
    assert result["average_budget"] == 0
    assert result["members_with_budgets"] == 0


def test_compute_budget_range_with_nulls():
    """Test budget range with null values (no limit)."""
    preferences = [
        {
            "budget": {
                "min_budget": None,
                "max_budget": 1000
            }
        },
        {
            "budget": {
                "min_budget": 500,
                "max_budget": None
            }
        }
    ]

    result = compute_budget_range(preferences)

    # Only the first preference is included (has valid max_budget)
    # The second is filtered out because max_budget is None
    assert result["min_budget"] == 0  # min_budget is None, treated as 0
    assert result["max_budget"] == 1000
    assert result["members_with_budgets"] == 1  # Only 1 valid budget


# ============================================================================
# Test intersect_vibes
# ============================================================================


def test_intersect_vibes_with_common_vibes():
    """Test vibe intersection with common vibes."""
    preferences = [
        {
            "destination_prefs": {
                "vibes": ["Beach", "Relaxation", "Food-focused"]
            }
        },
        {
            "destination_prefs": {
                "vibes": ["Beach", "Relaxation", "Nightlife"]
            }
        },
        {
            "destination_prefs": {
                "vibes": ["Beach", "Relaxation"]
            }
        }
    ]

    result = intersect_vibes(preferences)

    assert result["has_common_vibes"] is True
    assert set(result["common_vibes"]) == {"Beach", "Relaxation"}
    assert set(result["all_vibes"]) == {"Beach", "Relaxation", "Food-focused", "Nightlife"}
    assert result["vibe_counts"]["Beach"] == 3
    assert result["vibe_counts"]["Relaxation"] == 3
    assert result["vibe_counts"]["Food-focused"] == 1
    assert result["members_with_vibes"] == 3


def test_intersect_vibes_no_common_vibes():
    """Test vibe intersection with no common vibes."""
    preferences = [
        {
            "destination_prefs": {
                "vibes": ["Beach", "Relaxation"]
            }
        },
        {
            "destination_prefs": {
                "vibes": ["City", "Nightlife"]
            }
        },
        {
            "destination_prefs": {
                "vibes": ["Nature", "Adventure"]
            }
        }
    ]

    result = intersect_vibes(preferences)

    assert result["has_common_vibes"] is False
    assert result["common_vibes"] == []
    assert len(result["all_vibes"]) == 6
    assert result["members_with_vibes"] == 3


def test_intersect_vibes_empty_preferences():
    """Test vibe intersection with no vibe preferences."""
    preferences = [
        {"dates": {"earliest_start": "2025-06-01"}},
        {"budget": {"max_budget": 1000}}
    ]

    result = intersect_vibes(preferences)

    assert result["has_common_vibes"] is False
    assert result["common_vibes"] == []
    assert result["all_vibes"] == []
    assert result["vibe_counts"] == {}
    assert result["members_with_vibes"] == 0


def test_intersect_vibes_single_member():
    """Test vibe intersection with single member."""
    preferences = [
        {
            "destination_prefs": {
                "vibes": ["Beach", "Relaxation"]
            }
        }
    ]

    result = intersect_vibes(preferences)

    assert result["has_common_vibes"] is True
    assert set(result["common_vibes"]) == {"Beach", "Relaxation"}
    assert set(result["all_vibes"]) == {"Beach", "Relaxation"}
    assert result["members_with_vibes"] == 1


# ============================================================================
# Test extract_hard_constraints
# ============================================================================


def test_extract_hard_constraints_with_all_types():
    """Test constraint extraction with all constraint types."""
    preferences = [
        {
            "constraints": {
                "dietary_restrictions": ["vegetarian", "gluten-free"],
                "accessibility_needs": ["wheelchair accessible"],
                "hard_nos": "No camping, no red-eye flights"
            }
        },
        {
            "constraints": {
                "dietary_restrictions": ["vegan"],
                "accessibility_needs": ["wheelchair accessible", "hearing accessible"],
                "hard_nos": "No cruises"
            }
        },
        {
            "constraints": {
                "dietary_restrictions": ["vegetarian"],
                "hard_nos": "No extreme sports"
            }
        }
    ]

    result = extract_hard_constraints(preferences)

    assert set(result["dietary_restrictions"]) == {"vegetarian", "vegan", "gluten-free"}
    assert set(result["accessibility_needs"]) == {"wheelchair accessible", "hearing accessible"}
    assert len(result["hard_nos"]) == 3
    assert "No camping, no red-eye flights" in result["hard_nos"]
    assert "No cruises" in result["hard_nos"]
    assert "No extreme sports" in result["hard_nos"]
    assert result["members_with_constraints"] == 3


def test_extract_hard_constraints_empty_preferences():
    """Test constraint extraction with no constraints."""
    preferences = [
        {"dates": {"earliest_start": "2025-06-01"}},
        {"budget": {"max_budget": 1000}}
    ]

    result = extract_hard_constraints(preferences)

    assert result["dietary_restrictions"] == []
    assert result["accessibility_needs"] == []
    assert result["hard_nos"] == []
    assert result["members_with_constraints"] == 0


def test_extract_hard_constraints_with_duplicates():
    """Test constraint extraction with duplicate values."""
    preferences = [
        {
            "constraints": {
                "dietary_restrictions": ["vegetarian"],
                "accessibility_needs": ["wheelchair accessible"]
            }
        },
        {
            "constraints": {
                "dietary_restrictions": ["vegetarian"],  # Duplicate
                "accessibility_needs": ["wheelchair accessible"]  # Duplicate
            }
        }
    ]

    result = extract_hard_constraints(preferences)

    # Duplicates should be deduplicated (sets)
    assert result["dietary_restrictions"] == ["vegetarian"]
    assert result["accessibility_needs"] == ["wheelchair accessible"]
    assert result["members_with_constraints"] == 2


def test_extract_hard_constraints_with_empty_strings():
    """Test constraint extraction with empty strings."""
    preferences = [
        {
            "constraints": {
                "dietary_restrictions": ["vegetarian"],
                "hard_nos": ""  # Empty string should be ignored
            }
        },
        {
            "constraints": {
                "hard_nos": "   "  # Whitespace only should be ignored
            }
        }
    ]

    result = extract_hard_constraints(preferences)

    assert result["dietary_restrictions"] == ["vegetarian"]
    assert result["hard_nos"] == []  # Empty strings ignored
    assert result["members_with_constraints"] == 2


# ============================================================================
# Integration Test: All Tools Together
# ============================================================================


def test_all_tools_together():
    """Test all computation tools with realistic preference data."""
    preferences = [
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
                "dietary_restrictions": ["vegan"],
                "hard_nos": "No red-eye flights"
            }
        }
    ]

    # Date overlap
    date_result = compute_date_overlap(preferences)
    assert date_result["has_overlap"] is True
    assert date_result["overlap_days"] == 11

    # Budget range
    budget_result = compute_budget_range(preferences)
    assert budget_result["has_feasible_range"] is True
    assert budget_result["min_budget"] == 800
    assert budget_result["max_budget"] == 1500

    # Vibes
    vibe_result = intersect_vibes(preferences)
    assert vibe_result["has_common_vibes"] is True
    assert "Beach" in vibe_result["common_vibes"]

    # Constraints
    constraint_result = extract_hard_constraints(preferences)
    assert "vegetarian" in constraint_result["dietary_restrictions"]
    assert "vegan" in constraint_result["dietary_restrictions"]
    assert len(constraint_result["hard_nos"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
