"""
Unit tests for recommendation agents.

Tests agent creation and Pydantic model validation for:
- CandidateDestinationGeneratorAgent
- DestinationResearchAgent
- DestinationRankerAgent
"""

import pytest
from tripsync.recommendation_agents import (
    create_candidate_generator_agent,
    create_destination_research_agent,
    create_destination_ranker_agent,
    DestinationCandidate,
    DestinationResearchFacts,
    DestinationOption,
    RecommendationsPack,
    MoneyRange,
    Tradeoff,
)


# ============================================================================
# Agent Creation Tests
# ============================================================================


def test_create_candidate_generator_agent():
    """Test that CandidateDestinationGeneratorAgent can be created."""
    agent = create_candidate_generator_agent()
    assert agent is not None
    assert agent.name == 'candidate_destination_generator'
    assert 'gemini' in agent.model.lower()
    assert agent.description is not None
    assert len(agent.instruction) > 100  # Has substantial instructions


def test_create_destination_research_agent():
    """Test that DestinationResearchAgent can be created with Google Search tool."""
    agent = create_destination_research_agent()
    assert agent is not None
    assert agent.name == 'destination_research'
    assert 'gemini' in agent.model.lower()
    assert agent.description is not None
    assert len(agent.instruction) > 100
    # Verify Google Search tool is attached
    assert agent.tools is not None
    assert len(agent.tools) == 1  # Only one tool (ADK constraint)


def test_create_destination_ranker_agent():
    """Test that DestinationRankerAgent can be created."""
    agent = create_destination_ranker_agent()
    assert agent is not None
    assert agent.name == 'destination_ranker'
    assert 'gemini' in agent.model.lower()
    assert agent.description is not None
    assert len(agent.instruction) > 100


# ============================================================================
# Pydantic Model Tests
# ============================================================================


def test_money_range_model():
    """Test MoneyRange model validation."""
    money = MoneyRange(
        currency="USD",
        per_person_low=800,
        per_person_high=1500,
        includes=["accommodation", "food", "activities"]
    )
    assert money.currency == "USD"
    assert money.per_person_low == 800
    assert money.per_person_high == 1500
    assert len(money.includes) == 3


def test_money_range_defaults():
    """Test MoneyRange with default values."""
    money = MoneyRange(per_person_low=500, per_person_high=1000)
    assert money.currency == "USD"  # Default
    assert money.includes == []  # Default empty list


def test_tradeoff_model():
    """Test Tradeoff model validation."""
    tradeoff = Tradeoff(
        title="Slightly over budget",
        description="May exceed Alex's max by $200",
        severity="low"
    )
    assert tradeoff.title == "Slightly over budget"
    assert tradeoff.severity == "low"


def test_tradeoff_severity_validation():
    """Test that Tradeoff only accepts valid severity levels."""
    # Valid severities
    for severity in ["low", "medium", "high"]:
        tradeoff = Tradeoff(title="Test", description="Test", severity=severity)
        assert tradeoff.severity == severity

    # Invalid severity should raise validation error
    with pytest.raises(Exception):  # Pydantic ValidationError
        Tradeoff(title="Test", description="Test", severity="extreme")


def test_destination_candidate_model():
    """Test DestinationCandidate model validation."""
    candidate = DestinationCandidate(
        name="Lisbon",
        region="Portugal",
        reasoning="Perfect for city + culture vibes, mid-budget",
        diversity_category="city"
    )
    assert candidate.name == "Lisbon"
    assert candidate.region == "Portugal"
    assert "culture" in candidate.reasoning


def test_destination_research_facts_model():
    """Test DestinationResearchFacts model validation."""
    facts = DestinationResearchFacts(
        destination_name="Lisbon",
        facts=[
            "Average cost $80-150 per day",
            "Best time: April-October",
            "Great public transport"
        ],
        sources=["https://example.com/lisbon-guide"],
        typical_cost_signals="$80-150 per day",
        seasonality_notes="Best in May-June",
        two_day_highlights=[
            "Day 1: Alfama + Tram 28",
            "Day 2: Belém monuments"
        ]
    )
    assert facts.destination_name == "Lisbon"
    assert len(facts.facts) == 3
    assert len(facts.sources) == 1
    assert len(facts.two_day_highlights) == 2


def test_destination_research_facts_optional_fields():
    """Test DestinationResearchFacts with optional fields as None."""
    facts = DestinationResearchFacts(
        destination_name="Unknown City",
        facts=["Limited information available"]
    )
    assert facts.typical_cost_signals is None
    assert facts.seasonality_notes is None
    assert facts.sources == []  # Default empty list
    assert facts.two_day_highlights == []  # Default empty list


def test_destination_option_model():
    """Test DestinationOption model validation (final recommendation)."""
    option = DestinationOption(
        name="Lisbon",
        region="Portugal",
        why_it_fits=[
            "Matches city + culture vibes",
            "Within budget range",
            "Great weather in June"
        ],
        estimated_cost=MoneyRange(per_person_low=900, per_person_high=1400),
        sample_highlights_2day=[
            "Day 1: Historic Alfama",
            "Day 2: Belém monuments"
        ],
        tradeoffs=[],
        confidence="high",
        sources=["https://example.com/lisbon"]
    )
    assert option.name == "Lisbon"
    assert len(option.why_it_fits) == 3
    assert option.confidence == "high"
    assert option.estimated_cost.per_person_low == 900


def test_destination_option_with_tradeoffs():
    """Test DestinationOption with tradeoffs."""
    option = DestinationOption(
        name="Paris",
        region="France",
        why_it_fits=["Classic city destination"],
        estimated_cost=MoneyRange(per_person_low=1500, per_person_high=2200),
        sample_highlights_2day=["Eiffel Tower", "Louvre"],
        tradeoffs=[
            Tradeoff(
                title="Over budget",
                description="Exceeds group's max by $400",
                severity="medium"
            )
        ],
        confidence="medium",
        sources=[]
    )
    assert len(option.tradeoffs) == 1
    assert option.tradeoffs[0].severity == "medium"
    assert option.confidence == "medium"


def test_destination_option_confidence_validation():
    """Test that DestinationOption only accepts valid confidence levels."""
    # Valid confidence levels
    for confidence in ["low", "medium", "high"]:
        option = DestinationOption(
            name="Test",
            region="Test",
            why_it_fits=["test"],
            estimated_cost=MoneyRange(per_person_low=500, per_person_high=1000),
            sample_highlights_2day=["test"],
            confidence=confidence,
        )
        assert option.confidence == confidence

    # Invalid confidence should raise validation error
    with pytest.raises(Exception):  # Pydantic ValidationError
        DestinationOption(
            name="Test",
            region="Test",
            why_it_fits=["test"],
            estimated_cost=MoneyRange(per_person_low=500, per_person_high=1000),
            sample_highlights_2day=["test"],
            confidence="very_high",
        )


def test_recommendations_pack_model():
    """Test RecommendationsPack model validation (final output)."""
    pack = RecommendationsPack(
        trip_id="trip-123",
        generated_at_iso="2026-01-30T12:00:00Z",
        group_summary={
            "dates": "June 1-15",
            "budget": "$800-1500 per person",
            "vibes": "beach, relaxation, culture"
        },
        conflicts=["No date overlap between Alice and Bob"],
        options=[
            DestinationOption(
                name="Lisbon",
                region="Portugal",
                why_it_fits=["City + culture", "Budget fit"],
                estimated_cost=MoneyRange(per_person_low=900, per_person_high=1400),
                sample_highlights_2day=["Alfama", "Belém"],
                confidence="high",
            ),
            DestinationOption(
                name="Tulum",
                region="Mexico",
                why_it_fits=["Beach + relaxation"],
                estimated_cost=MoneyRange(per_person_low=800, per_person_high=1200),
                sample_highlights_2day=["Beach day", "Cenote swim"],
                confidence="medium",
            ),
            DestinationOption(
                name="Algarve",
                region="Portugal",
                why_it_fits=["Beach + culture mix"],
                estimated_cost=MoneyRange(per_person_low=850, per_person_high=1300),
                sample_highlights_2day=["Beach town", "Coastal hike"],
                confidence="high",
            ),
        ]
    )
    assert pack.trip_id == "trip-123"
    assert len(pack.options) == 3
    assert len(pack.conflicts) == 1
    assert "beach" in pack.group_summary["vibes"]


def test_recommendations_pack_requires_3_to_5_options():
    """Test that RecommendationsPack requires 3-5 options."""
    # Valid: 3 options
    pack_3 = RecommendationsPack(
        trip_id="trip-123",
        generated_at_iso="2026-01-30T12:00:00Z",
        group_summary={},
        options=[
            DestinationOption(
                name=f"Destination {i}",
                region="Region",
                why_it_fits=["fits"],
                estimated_cost=MoneyRange(per_person_low=500, per_person_high=1000),
                sample_highlights_2day=["activity"],
                confidence="medium",
            )
            for i in range(3)
        ]
    )
    assert len(pack_3.options) == 3

    # Valid: 5 options
    pack_5 = RecommendationsPack(
        trip_id="trip-123",
        generated_at_iso="2026-01-30T12:00:00Z",
        group_summary={},
        options=[
            DestinationOption(
                name=f"Destination {i}",
                region="Region",
                why_it_fits=["fits"],
                estimated_cost=MoneyRange(per_person_low=500, per_person_high=1000),
                sample_highlights_2day=["activity"],
                confidence="medium",
            )
            for i in range(5)
        ]
    )
    assert len(pack_5.options) == 5

    # Invalid: 2 options (less than min_length=3)
    with pytest.raises(Exception):  # Pydantic ValidationError
        RecommendationsPack(
            trip_id="trip-123",
            generated_at_iso="2026-01-30T12:00:00Z",
            group_summary={},
            options=[
                DestinationOption(
                    name=f"Destination {i}",
                    region="Region",
                    why_it_fits=["fits"],
                    estimated_cost=MoneyRange(per_person_low=500, per_person_high=1000),
                    sample_highlights_2day=["activity"],
                    confidence="medium",
                )
                for i in range(2)
            ]
        )

    # Invalid: 6 options (more than max_length=5)
    with pytest.raises(Exception):  # Pydantic ValidationError
        RecommendationsPack(
            trip_id="trip-123",
            generated_at_iso="2026-01-30T12:00:00Z",
            group_summary={},
            options=[
                DestinationOption(
                    name=f"Destination {i}",
                    region="Region",
                    why_it_fits=["fits"],
                    estimated_cost=MoneyRange(per_person_low=500, per_person_high=1000),
                    sample_highlights_2day=["activity"],
                    confidence="medium",
                )
                for i in range(6)
            ]
        )


def test_recommendations_pack_empty_conflicts():
    """Test RecommendationsPack with no conflicts."""
    pack = RecommendationsPack(
        trip_id="trip-123",
        generated_at_iso="2026-01-30T12:00:00Z",
        group_summary={"dates": "Flexible"},
        options=[
            DestinationOption(
                name=f"Destination {i}",
                region="Region",
                why_it_fits=["fits"],
                estimated_cost=MoneyRange(per_person_low=500, per_person_high=1000),
                sample_highlights_2day=["activity"],
                confidence="medium",
            )
            for i in range(3)
        ]
    )
    assert pack.conflicts == []  # Default empty list


# ============================================================================
# Integration Test
# ============================================================================


def test_full_recommendation_pipeline_structure():
    """
    Test that all agents and models work together in the expected pipeline.
    This is a structural test, not an execution test (would need ADK runtime).
    """
    # 1. Create all agents
    generator = create_candidate_generator_agent()
    researcher = create_destination_research_agent()
    ranker = create_destination_ranker_agent()

    assert generator is not None
    assert researcher is not None
    assert ranker is not None

    # 2. Simulate the data flow with Pydantic models
    # Step 1: Generator produces candidates
    candidates = [
        DestinationCandidate(
            name="Lisbon",
            region="Portugal",
            reasoning="City + culture fit",
            diversity_category="city"
        ),
        DestinationCandidate(
            name="Tulum",
            region="Mexico",
            reasoning="Beach + relaxation fit",
            diversity_category="beach"
        ),
    ]
    assert len(candidates) == 2

    # Step 2: Researcher produces facts
    research = {
        "Lisbon": DestinationResearchFacts(
            destination_name="Lisbon",
            facts=["Cost: $80-150/day", "Best: May-June"],
            sources=["https://example.com/lisbon"]
        ),
        "Tulum": DestinationResearchFacts(
            destination_name="Tulum",
            facts=["Cost: $60-120/day", "Best: Nov-Apr"],
            sources=["https://example.com/tulum"]
        ),
    }
    assert len(research) == 2

    # Step 3: Ranker produces options
    options = [
        DestinationOption(
            name="Lisbon",
            region="Portugal",
            why_it_fits=["City + culture", "Budget fit"],
            estimated_cost=MoneyRange(per_person_low=900, per_person_high=1400),
            sample_highlights_2day=["Alfama", "Belém"],
            confidence="high",
            sources=research["Lisbon"].sources,
        ),
        DestinationOption(
            name="Tulum",
            region="Mexico",
            why_it_fits=["Beach + relaxation"],
            estimated_cost=MoneyRange(per_person_low=800, per_person_high=1200),
            sample_highlights_2day=["Beach", "Cenote"],
            confidence="medium",
            sources=research["Tulum"].sources,
        ),
        DestinationOption(
            name="Barcelona",
            region="Spain",
            why_it_fits=["City + beach + food"],
            estimated_cost=MoneyRange(per_person_low=1000, per_person_high=1600),
            sample_highlights_2day=["Sagrada Familia", "Beach"],
            confidence="high",
        ),
    ]
    assert len(options) == 3

    # Step 4: Create final RecommendationsPack
    pack = RecommendationsPack(
        trip_id="trip-123",
        generated_at_iso="2026-01-30T12:00:00Z",
        group_summary={"dates": "June 1-15", "budget": "$800-1500"},
        conflicts=[],
        options=options
    )

    assert pack.trip_id == "trip-123"
    assert len(pack.options) == 3
    assert all(opt.confidence in ["low", "medium", "high"] for opt in pack.options)
    assert all(len(opt.why_it_fits) > 0 for opt in pack.options)

    print("✓ Full recommendation pipeline structure validated")
