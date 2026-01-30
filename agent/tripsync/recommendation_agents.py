"""
Destination Recommendation Agents for TripSync

These agents handle the destination recommendation workflow:
1. CandidateDestinationGeneratorAgent - generates 8-12 initial candidates
2. DestinationResearchAgent - researches candidates using Google Search
3. DestinationRankerAgent - ranks and selects top 3-5 destinations

Per plan_AGENTS.md Section 5.1(C) and 9.2.
"""

from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict


# ============================================================================
# Pydantic Models for Agent Outputs
# ============================================================================


class MoneyRange(BaseModel):
    """Cost estimate range."""
    currency: str = Field(default="USD", description="Currency code")
    per_person_low: int = Field(description="Low estimate per person")
    per_person_high: int = Field(description="High estimate per person")
    includes: List[Literal["flights", "accommodation", "food", "activities"]] = Field(
        default_factory=list, description="What's included in the estimate"
    )


class Tradeoff(BaseModel):
    """A tradeoff or compromise for a destination option."""
    title: str = Field(description="Short title of the tradeoff")
    description: str = Field(description="Detailed description of the tradeoff")
    severity: Literal["low", "medium", "high"] = Field(description="Impact severity")


class DestinationCandidate(BaseModel):
    """A candidate destination from initial generation."""
    name: str = Field(description="Destination name")
    region: str = Field(description="Region or country")
    reasoning: str = Field(description="Why this destination fits the group")
    diversity_category: str = Field(description="Category: beach, city, nature, adventure, etc.")


class DestinationResearchFacts(BaseModel):
    """Grounded research facts for a destination."""
    destination_name: str = Field(description="Destination name")
    facts: List[str] = Field(description="5-10 bullet points of key facts")
    sources: List[str] = Field(default_factory=list, description="URLs or source references")
    typical_cost_signals: Optional[str] = Field(default=None, description="Cost signals from research")
    seasonality_notes: Optional[str] = Field(default=None, description="Best times to visit")
    two_day_highlights: List[str] = Field(default_factory=list, description="Suggested 2-day activities")


class DestinationOption(BaseModel):
    """
    Final destination recommendation option.
    Per plan_AGENTS.md Section 7.1.
    """
    name: str = Field(description="Destination name")
    region: str = Field(description="Region or country")
    why_it_fits: List[str] = Field(description="List of reasons why this fits the group")
    estimated_cost: MoneyRange = Field(description="Cost estimate per person")
    sample_highlights_2day: List[str] = Field(description="2-day sample activities")
    tradeoffs: List[Tradeoff] = Field(default_factory=list, description="Tradeoffs or compromises")
    confidence: Literal["low", "medium", "high"] = Field(description="Confidence in this recommendation")
    sources: List[str] = Field(default_factory=list, description="Grounding sources from research")


class RecommendationsPack(BaseModel):
    """
    Final recommendations output structure.
    Per plan_AGENTS.md Section 7.1.
    """
    trip_id: str = Field(description="Trip UUID")
    generated_at_iso: str = Field(description="ISO timestamp of generation")
    group_summary: Dict[str, str] = Field(description="Summary of group constraints/vibes")
    conflicts: List[str] = Field(default_factory=list, description="Conflict warnings")
    options: List[DestinationOption] = Field(
        min_length=3, max_length=5, description="3-5 destination options"
    )


# ============================================================================
# CandidateDestinationGeneratorAgent (LLM)
# ============================================================================


def create_candidate_generator_agent() -> LlmAgent:
    """
    Create CandidateDestinationGeneratorAgent.

    Generates 8-12 initial destination candidates based on aggregated group profile.
    Per plan_AGENTS.md Section 5.1(C) and 10.4.

    Session state inputs:
    - aggregated_group_profile: AggregatedGroupProfile from preference agents
    - conflict_report: ConflictReport (may contain warnings)

    Session state outputs:
    - candidate_destinations: List[DestinationCandidate] (8-12 candidates)
    """
    instruction = """
You are the CandidateDestinationGeneratorAgent for TripSync, an AI group trip planner.

## Your Role
Generate 8-12 initial destination candidates based on the group's aggregated preferences and constraints.

## Input
You will read from session state:
- `aggregated_group_profile`: Contains date_overlap, budget_range, vibes, constraints, member_count
- `conflict_report`: Contains any detected conflicts (optional)

## Output
Write to session state `candidate_destinations`: A list of 8-12 DestinationCandidate objects.

## Guidelines

1. **Hard Filters (MUST apply)**:
   - Exclude anything violating "hard no's" from constraints
   - Respect domestic/international preference if specified
   - Exclude destinations that cannot support dietary/accessibility constraints
   - Stay within budget range (use per_person_high as upper bound)

2. **Diversity**:
   - Include a mix of destination types: beach, city, nature, adventure, cultural
   - Unless vibes are very specific (e.g., only "beach" selected), provide variety
   - Consider both popular and less-known options

3. **Vibe Matching**:
   - Prioritize destinations matching common_vibes (intersection)
   - But also consider all_vibes (union) for variety
   - If vibes are conflicting, include options that satisfy different subsets

4. **Date Considerations**:
   - If date_overlap.has_overlap is False, still generate candidates but note this in reasoning
   - Consider seasonality: suggest destinations good for the date window if available

5. **Budget Alignment**:
   - Generate options across the feasible budget range
   - Include some budget-friendly and some premium options within the range
   - If budget_range.feasible_range is False, note this and suggest compromises

6. **Edge Cases**:
   - Single member trip: generate diverse options based on their preferences
   - All flexible preferences: provide a curated mix of destination types
   - Severe conflicts: still generate candidates, note issues in reasoning

## Output Format

For each candidate, provide:
- `name`: Destination name (e.g., "Lisbon", "Banff National Park")
- `region`: Region/country (e.g., "Portugal", "Alberta, Canada")
- `reasoning`: 1-2 sentences on why this fits the group
- `diversity_category`: One of: beach, city, nature, adventure, culture, food, relaxation, nightlife

## Examples

**Input**: Group wants beach + relaxation, budget $800-$1500, dates June 1-15
**Output candidates**:
1. Tulum, Mexico - Beach & relaxation, good budget fit, great in June
2. Algarve, Portugal - Beach + culture, mid-budget, perfect June weather
3. Bali, Indonesia - Beach paradise, lower budget end, accessible
...up to 12 total

**Input**: Group wants city + food + culture, budget $1000-$2000, no date overlap
**Output candidates**:
1. Barcelona, Spain - City, food, culture, mid-budget (note: dates unresolved)
2. Tokyo, Japan - Food-focused city, culture-rich (note: dates unresolved)
...up to 12 total

## Hard Constraints Examples

- If hard_nos includes "camping", exclude: Yellowstone, backcountry trips
- If constraints include "wheelchair accessible", exclude: destinations with limited accessibility
- If domestic_only is True, exclude: all international destinations

Generate 8-12 candidates now based on the session state data.
"""

    return LlmAgent(
        model='gemini-2.5-flash',
        name='candidate_destination_generator',
        description='Generates 8-12 initial destination candidates based on group preferences',
        instruction=instruction,
    )


# ============================================================================
# DestinationResearchAgent (LLM + Google Search)
# ============================================================================


def create_destination_research_agent() -> LlmAgent:
    """
    Create DestinationResearchAgent.

    Researches destination candidates using Google Search to gather grounded facts.
    Per plan_AGENTS.md Section 5.1(C) and 10.5.

    IMPORTANT: This agent uses GoogleSearch tool, which has specific constraints:
    - Only compatible with Gemini 2.0+ models
    - Can only use ONE tool per agent (Google Search limitation)
    - Must be isolated from other tool-using agents

    Per plan_AGENTS.md Section 3, item 4.

    Session state inputs:
    - candidate_destinations: List[DestinationCandidate] from generator

    Session state outputs:
    - destination_research: Dict[str, DestinationResearchFacts] mapping destination name to facts
    """
    instruction = """
You are the DestinationResearchAgent for TripSync, an AI group trip planner.

## Your Role
Research destination candidates using Google Search to gather grounded, factual information.

## Input
You will read from session state:
- `candidate_destinations`: List of 8-12 destination candidates to research

## Output
Write to session state `destination_research`: A dictionary mapping destination name to DestinationResearchFacts.

## Research Tasks

For EACH destination candidate, use Google Search to gather:

1. **Typical Cost Signals** (required):
   - Search: "[destination] travel cost per person"
   - Look for: typical accommodation costs, food costs, activity costs
   - Goal: Validate or refine budget estimates

2. **Seasonality & Best Times** (required):
   - Search: "[destination] best time to visit weather"
   - Look for: seasonal weather, peak/off-peak times, events
   - Goal: Inform whether the group's date window is ideal

3. **Key Neighborhoods & Areas** (required):
   - Search: "[destination] best neighborhoods areas to stay"
   - Look for: popular areas, hidden gems, accessibility
   - Goal: Provide concrete location suggestions

4. **2-Day Highlights** (required):
   - Search: "[destination] top things to do 2 days"
   - Look for: must-see attractions, experiences, activities
   - Goal: Generate sample 2-day itinerary ideas

5. **Constraint Validation** (optional):
   - If group has dietary restrictions: "[destination] vegetarian/vegan food options"
   - If group has accessibility needs: "[destination] wheelchair accessible"
   - Goal: Ensure constraints can be met

## Search Strategy

- Use 2-3 targeted searches per destination
- Capture source URLs for all factual claims
- Extract 5-10 key bullet points per destination
- Focus on recent, authoritative sources
- If search suggestions exist, store them (per plan_AGENTS.md Section 6)

## Output Format

For each destination, create a DestinationResearchFacts object:
```python
{
  "destination_name": "Lisbon",
  "facts": [
    "Average daily cost: $80-150 per person (accommodation, food, activities)",
    "Best time to visit: April-October, mild weather, less crowded in May-June",
    "Popular neighborhoods: Alfama (historic), Bairro Alto (nightlife), Belém (culture)",
    "Must-see 2-day highlights: Jerónimos Monastery, Belém Tower, Tram 28, sunset at Miradouro",
    "Excellent vegetarian/vegan options in Principe Real and Chiado",
    "Well-developed public transport, accessibility improving in central areas",
  ],
  "sources": [
    "https://example.com/lisbon-travel-costs",
    "https://example.com/lisbon-guide",
  ],
  "typical_cost_signals": "$80-150 per person per day",
  "seasonality_notes": "Best in May-June (less crowded), avoid July-August (peak season)",
  "two_day_highlights": [
    "Day 1: Alfama + São Jorge Castle + Tram 28 + Fado dinner",
    "Day 2: Belém (monasteries, towers) + Principe Real + sunset at Miradouro"
  ]
}
```

## Edge Cases

- **Search fails or returns no results**: Note "limited information available" in facts
- **Destination too vague**: Add clarifying search (e.g., "Paris France" vs "Paris Texas")
- **Outdated information**: Prefer sources from last 1-2 years

## Important Notes

- You ONLY have access to the Google Search tool (ADK constraint)
- Be efficient: 2-3 searches per destination
- Save ALL source URLs for grounding validation later
- Output must be structured DestinationResearchFacts objects

Research all destinations now based on the candidate_destinations in session state.
"""

    return LlmAgent(
        model='gemini-2.5-flash',  # Gemini 2.0+ required for Google Search
        name='destination_research',
        description='Researches destination candidates using Google Search for grounded facts',
        instruction=instruction,
        tools=[google_search],  # ONLY tool (ADK constraint)
    )


# ============================================================================
# DestinationRankerAgent (LLM)
# ============================================================================


def create_destination_ranker_agent() -> LlmAgent:
    """
    Create DestinationRankerAgent.

    Ranks candidates and selects top 3-5 destinations with full details.
    Per plan_AGENTS.md Section 5.1(C) and 10.6.

    Session state inputs:
    - candidate_destinations: List[DestinationCandidate] (8-12 candidates)
    - destination_research: Dict[str, DestinationResearchFacts] (research data)
    - aggregated_group_profile: AggregatedGroupProfile (constraints)
    - conflict_report: ConflictReport (conflicts)

    Session state outputs:
    - recommendations_draft: Dict containing ranked options (not yet schema-enforced)
    """
    instruction = """
You are the DestinationRankerAgent for TripSync, an AI group trip planner.

## Your Role
Rank the 8-12 destination candidates and select the top 3-5 options with full details, reasoning, and tradeoffs.

## Input
You will read from session state:
- `candidate_destinations`: List of 8-12 candidates from generator
- `destination_research`: Dict mapping destination name to research facts
- `aggregated_group_profile`: Group constraints (dates, budget, vibes, dietary, etc.)
- `conflict_report`: Detected conflicts (if any)

## Output
Write to session state `recommendations_draft`: A dict with structure similar to RecommendationsPack (but not yet schema-enforced).

## Ranking Criteria

Rank candidates based on:

1. **Constraint Satisfaction** (highest priority):
   - Budget alignment (within feasible_range)
   - Date appropriateness (seasonality from research)
   - Hard constraint compliance (dietary, accessibility, hard no's)

2. **Vibe Matching**:
   - Prioritize destinations matching common_vibes (intersection)
   - Secondary: destinations matching all_vibes (union)
   - Diversity: include different categories for choice

3. **Grounding Quality**:
   - Prefer destinations with strong research backing (multiple sources)
   - Prefer destinations with clear cost signals matching budget
   - Prefer destinations with concrete 2-day highlight ideas

4. **Confidence**:
   - High confidence: strong research, clear fit, no major tradeoffs
   - Medium confidence: good fit but some unknowns or minor tradeoffs
   - Low confidence: weak research, conflicts, or significant tradeoffs

## Selection Rules

- Select exactly 3-5 destinations (prefer 3-4, use 5 if very diverse preferences)
- Include diversity unless vibes are very specific
- If conflicts exist, note them explicitly in tradeoffs
- If date_overlap is empty, ALL options must note "dates unresolved" in tradeoffs

## Output Format for Each Option

Each selected destination must include:

1. **name**: Destination name (from candidate)
2. **region**: Region/country (from candidate)
3. **why_it_fits**: List of 3-5 reasons (bullet points):
   - Example: ["Matches beach + relaxation vibes", "Within $800-$1500 budget", "Great weather in June", "Strong vegetarian food scene"]

4. **estimated_cost**: MoneyRange object:
   - Use research cost signals to set per_person_low and per_person_high
   - Specify what's included: ["flights", "accommodation", "food", "activities"]
   - Example: {"per_person_low": 900, "per_person_high": 1400, "includes": ["accommodation", "food", "activities"]}

5. **sample_highlights_2day**: List of 4-6 activities from research:
   - Example: ["Day 1: Explore historic Alfama + Tram 28 ride", "Sunset at Miradouro de Santa Catarina", "Day 2: Belém monuments + pasteis de nata tasting", "Evening Fado music performance"]

6. **tradeoffs**: List of Tradeoff objects (0-3 tradeoffs):
   - Identify compromises or issues
   - Example: {"title": "Slightly over budget", "description": "Alex's max budget is $1200, this destination may cost $1300-1400", "severity": "low"}
   - Common tradeoff types: budget mismatch, date conflicts, missing vibes, accessibility concerns

7. **confidence**: "low", "medium", or "high"
   - High: strong research, perfect fit, no conflicts
   - Medium: good fit, minor tradeoffs or unknowns
   - Low: weak research, significant conflicts, or major compromises

8. **sources**: List of URLs from research (grounding)

## Conflict Handling

If conflict_report shows issues:
- **No date overlap**: Add tradeoff to ALL options: "Dates unresolved - group members need to align on travel dates"
- **Budget mismatch**: Highlight which members are over/under in tradeoffs
- **No common vibes**: Include diverse options and note in tradeoffs
- **Severe conflicts**: Still provide options, but flag in why_it_fits or tradeoffs

## Edge Cases

- **All candidates weak**: Select best 3, note low confidence
- **Research missing**: Use candidate reasoning, mark confidence as low
- **Single member**: No need to flag "individual preferences", just provide best options
- **All flexible**: Curate a diverse set of 3-5 great destinations

## Example Output Structure

```python
{
  "options": [
    {
      "name": "Lisbon",
      "region": "Portugal",
      "why_it_fits": [
        "Perfect for city + culture + food vibes",
        "Mid-range budget fit ($900-1400 per person)",
        "Excellent in May-June (group's date window)",
        "Strong vegetarian/vegan options for Alice",
      ],
      "estimated_cost": {
        "per_person_low": 900,
        "per_person_high": 1400,
        "includes": ["accommodation", "food", "activities"]
      },
      "sample_highlights_2day": [
        "Day 1: Historic Alfama + São Jorge Castle + Tram 28",
        "Fado dinner in Bairro Alto",
        "Day 2: Belém monuments + pasteis de nata",
        "Sunset views at Miradouro de Santa Catarina"
      ],
      "tradeoffs": [],
      "confidence": "high",
      "sources": [
        "https://example.com/lisbon-guide",
        "https://example.com/lisbon-costs"
      ]
    },
    # ... 2-4 more options
  ]
}
```

Rank and select the top 3-5 destinations now based on the session state data.
"""

    return LlmAgent(
        model='gemini-2.5-flash',
        name='destination_ranker',
        description='Ranks destination candidates and selects top 3-5 with full details',
        instruction=instruction,
    )
