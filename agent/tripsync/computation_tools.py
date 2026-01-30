"""
Computation Tools for TripSync Agents

Deterministic, non-LLM utility functions for preference aggregation.
These tools are used by AggregationAgent and ConflictDetectorAgent.

Per plan_AGENTS.md Section 8.2, these are custom Python functions, not LLM-based agents.
"""

from datetime import datetime, timedelta
from typing import Any


def compute_date_overlap(preferences: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Compute the date overlap window across all member preferences.

    Args:
        preferences: List of preference dictionaries with 'dates' field

    Returns:
        dict with:
          - overlap_start: earliest common start date (ISO string or null)
          - overlap_end: latest common end date (ISO string or null)
          - has_overlap: boolean
          - overlap_days: number of days in overlap (or 0)
          - members_with_dates: count of members who provided dates
    """
    # Filter preferences with date information
    date_prefs = [
        p for p in preferences
        if p.get("dates") and p["dates"].get("earliest_start") and p["dates"].get("latest_end")
    ]

    if not date_prefs:
        return {
            "overlap_start": None,
            "overlap_end": None,
            "has_overlap": False,
            "overlap_days": 0,
            "members_with_dates": 0
        }

    # Parse dates and find overlap
    earliest_starts = []
    latest_ends = []

    for pref in date_prefs:
        try:
            earliest_start = datetime.fromisoformat(pref["dates"]["earliest_start"].replace("Z", "+00:00"))
            latest_end = datetime.fromisoformat(pref["dates"]["latest_end"].replace("Z", "+00:00"))
            earliest_starts.append(earliest_start)
            latest_ends.append(latest_end)
        except (ValueError, KeyError):
            continue

    if not earliest_starts or not latest_ends:
        return {
            "overlap_start": None,
            "overlap_end": None,
            "has_overlap": False,
            "overlap_days": 0,
            "members_with_dates": len(date_prefs)
        }

    # Overlap window: latest of earliest_starts to earliest of latest_ends
    overlap_start = max(earliest_starts)
    overlap_end = min(latest_ends)

    has_overlap = overlap_start <= overlap_end
    overlap_days = max(0, (overlap_end - overlap_start).days + 1) if has_overlap else 0

    return {
        "overlap_start": overlap_start.isoformat() if has_overlap else None,
        "overlap_end": overlap_end.isoformat() if has_overlap else None,
        "has_overlap": has_overlap,
        "overlap_days": overlap_days,
        "members_with_dates": len(date_prefs)
    }


def compute_budget_range(preferences: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Compute the aggregated budget range across all member preferences.

    Args:
        preferences: List of preference dictionaries with 'budget' field

    Returns:
        dict with:
          - min_budget: minimum budget anyone can afford (max of all min_budgets)
          - max_budget: maximum budget anyone can afford (min of all max_budgets)
          - has_feasible_range: boolean (min_budget <= max_budget)
          - average_budget: average of all budgets
          - members_with_budgets: count of members who provided budgets
    """
    # Filter preferences with budget information
    budget_prefs = [
        p for p in preferences
        if p.get("budget") and isinstance(p["budget"].get("max_budget"), (int, float))
    ]

    if not budget_prefs:
        return {
            "min_budget": 0,
            "max_budget": 0,
            "has_feasible_range": False,
            "average_budget": 0,
            "members_with_budgets": 0
        }

    # Extract min and max budgets
    min_budgets = []
    max_budgets = []

    for pref in budget_prefs:
        budget = pref["budget"]
        min_budget = budget.get("min_budget", 0) or 0
        max_budget = budget.get("max_budget", 0) or 0

        min_budgets.append(min_budget)
        max_budgets.append(max_budget)

    # Aggregated budget range: max of mins, min of maxs
    aggregated_min = max(min_budgets) if min_budgets else 0
    aggregated_max = min(max_budgets) if max_budgets else 0

    has_feasible_range = aggregated_min <= aggregated_max

    # Calculate average budget (midpoint of each member's range)
    average_budget = sum((min_b + max_b) / 2 for min_b, max_b in zip(min_budgets, max_budgets)) / len(budget_prefs)

    return {
        "min_budget": aggregated_min,
        "max_budget": aggregated_max,
        "has_feasible_range": has_feasible_range,
        "average_budget": round(average_budget, 2),
        "members_with_budgets": len(budget_prefs)
    }


def intersect_vibes(preferences: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Compute the intersection and union of vibes across all member preferences.

    Args:
        preferences: List of preference dictionaries with 'destination_prefs' field

    Returns:
        dict with:
          - common_vibes: list of vibes ALL members want (intersection)
          - all_vibes: list of vibes ANY member wants (union)
          - has_common_vibes: boolean (common_vibes is non-empty)
          - vibe_counts: dict mapping each vibe to count of members who selected it
          - members_with_vibes: count of members who provided vibes
    """
    # Filter preferences with destination vibes
    vibe_prefs = [
        p for p in preferences
        if p.get("destination_prefs") and p["destination_prefs"].get("vibes")
    ]

    if not vibe_prefs:
        return {
            "common_vibes": [],
            "all_vibes": [],
            "has_common_vibes": False,
            "vibe_counts": {},
            "members_with_vibes": 0
        }

    # Extract vibes from each member
    all_vibe_sets = []
    vibe_counts: dict[str, int] = {}

    for pref in vibe_prefs:
        vibes = pref["destination_prefs"]["vibes"]
        if isinstance(vibes, list) and vibes:
            vibe_set = set(vibes)
            all_vibe_sets.append(vibe_set)

            # Count occurrences
            for vibe in vibe_set:
                vibe_counts[vibe] = vibe_counts.get(vibe, 0) + 1

    if not all_vibe_sets:
        return {
            "common_vibes": [],
            "all_vibes": [],
            "has_common_vibes": False,
            "vibe_counts": {},
            "members_with_vibes": len(vibe_prefs)
        }

    # Intersection: vibes ALL members want
    common_vibes = set.intersection(*all_vibe_sets)

    # Union: vibes ANY member wants
    all_vibes = set.union(*all_vibe_sets)

    return {
        "common_vibes": sorted(list(common_vibes)),
        "all_vibes": sorted(list(all_vibes)),
        "has_common_vibes": len(common_vibes) > 0,
        "vibe_counts": vibe_counts,
        "members_with_vibes": len(vibe_prefs)
    }


def extract_hard_constraints(preferences: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Extract and merge all hard constraints across member preferences.

    Args:
        preferences: List of preference dictionaries with 'constraints' field

    Returns:
        dict with:
          - dietary_restrictions: list of all unique dietary restrictions
          - accessibility_needs: list of all unique accessibility needs
          - hard_nos: list of all hard no's (deal-breakers)
          - members_with_constraints: count of members who provided constraints
    """
    # Filter preferences with constraints
    constraint_prefs = [
        p for p in preferences
        if p.get("constraints")
    ]

    if not constraint_prefs:
        return {
            "dietary_restrictions": [],
            "accessibility_needs": [],
            "hard_nos": [],
            "members_with_constraints": 0
        }

    # Aggregate constraints
    dietary_restrictions = set()
    accessibility_needs = set()
    hard_nos = []

    for pref in constraint_prefs:
        constraints = pref["constraints"]

        # Dietary restrictions
        if constraints.get("dietary_restrictions"):
            if isinstance(constraints["dietary_restrictions"], list):
                dietary_restrictions.update(constraints["dietary_restrictions"])

        # Accessibility needs
        if constraints.get("accessibility_needs"):
            if isinstance(constraints["accessibility_needs"], list):
                accessibility_needs.update(constraints["accessibility_needs"])

        # Hard no's (keep all, don't deduplicate as context matters)
        if constraints.get("hard_nos"):
            hard_no = constraints["hard_nos"]
            if isinstance(hard_no, str) and hard_no.strip():
                hard_nos.append(hard_no.strip())
            elif isinstance(hard_no, list):
                hard_nos.extend([h.strip() for h in hard_no if isinstance(h, str) and h.strip()])

    return {
        "dietary_restrictions": sorted(list(dietary_restrictions)),
        "accessibility_needs": sorted(list(accessibility_needs)),
        "hard_nos": hard_nos,
        "members_with_constraints": len(constraint_prefs)
    }
