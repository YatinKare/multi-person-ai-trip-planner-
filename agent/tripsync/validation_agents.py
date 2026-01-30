"""
Validation Agents for TripSync

These agents handle validation and schema enforcement for generated outputs:
1. SchemaEnforcerAgent - converts draft outputs to strict Pydantic models
2. ConstraintComplianceValidatorAgent - validates against hard constraints
3. GroundingValidatorAgent - ensures factual claims are backed by sources

Per plan_AGENTS.md Sections 5.1(E), 7, and 10.8-10.9.
"""

from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any


# ============================================================================
# Pydantic Models for Validation Outputs
# ============================================================================


class ValidationIssue(BaseModel):
    """A single validation issue found during compliance checking."""
    category: Literal["budget", "dates", "dietary", "accessibility", "hard_no", "other"] = Field(
        description="Category of constraint violation"
    )
    severity: Literal["error", "warning"] = Field(
        description="Severity: error blocks completion, warning is advisory"
    )
    description: str = Field(description="Clear description of the issue")
    affected_item: Optional[str] = Field(
        default=None, description="Which destination/activity/day is affected"
    )
    suggested_fix: Optional[str] = Field(
        default=None, description="How to resolve this issue"
    )


class ConstraintComplianceResult(BaseModel):
    """Result of constraint compliance validation."""
    is_valid: bool = Field(description="Overall pass/fail status")
    issues: List[ValidationIssue] = Field(
        default_factory=list, description="List of constraint violations found"
    )
    warnings: List[ValidationIssue] = Field(
        default_factory=list, description="Non-blocking warnings"
    )
    summary: str = Field(description="Human-readable summary of validation result")


class GroundingIssue(BaseModel):
    """An issue with grounding (factual claims without sources)."""
    claim: str = Field(description="The ungrounded factual claim")
    location: str = Field(description="Where the claim appears (destination/activity)")
    severity: Literal["error", "warning"] = Field(
        description="error if critical fact, warning if minor detail"
    )
    suggestion: Optional[str] = Field(
        default=None, description="Suggested research or clarification"
    )


class GroundingValidationResult(BaseModel):
    """Result of grounding validation."""
    is_grounded: bool = Field(description="Overall grounding status")
    issues: List[GroundingIssue] = Field(
        default_factory=list, description="Ungrounded claims found"
    )
    sources_count: int = Field(description="Number of sources provided")
    coverage_score: float = Field(
        description="Percentage of factual claims backed by sources (0-1)", ge=0, le=1
    )
    summary: str = Field(description="Human-readable summary of grounding quality")


# ============================================================================
# Agent Creation Functions
# ============================================================================


def create_schema_enforcer_agent_for_recommendations() -> LlmAgent:
    """
    Creates a SchemaEnforcerAgent for RecommendationsPack.

    This agent converts recommendations_draft (freeform) into structured RecommendationsPack.
    Uses output_schema to enforce strict Pydantic validation.
    Cannot use tools per ADK constraint (output_schema agents are tool-free).

    Per plan_AGENTS.md Section 10.8.

    Returns:
        LlmAgent configured for recommendation schema enforcement
    """
    # Import here to avoid circular dependency
    from .recommendation_agents import RecommendationsPack

    instruction = """You are the Schema Enforcer for TripSync recommendations.

Your job is to convert the recommendations_draft from session state into a strict RecommendationsPack schema.

**Inputs (from session state):**
- recommendations_draft: Freeform draft with 3-5 destination options
- trip_context: Trip ID and metadata
- aggregated_group_profile: Group summary for context
- conflict_report: Any conflicts to include

**Your Task:**
1. Parse the recommendations_draft and extract all relevant data
2. Structure it into the exact RecommendationsPack format:
   - trip_id: from trip_context
   - generated_at_iso: current ISO timestamp
   - group_summary: brief dict of constraints/vibes (2-3 key points)
   - conflicts: list of conflict strings from conflict_report (if any)
   - options: 3-5 DestinationOption objects, each with:
     - name, region, why_it_fits (list of 3-5 reasons)
     - estimated_cost (MoneyRange with per_person_low, per_person_high, includes list)
     - sample_highlights_2day (list of 4-6 activities)
     - tradeoffs (list of 0-3 Tradeoff objects with title, description, severity)
     - confidence (low/medium/high based on research quality)
     - sources (list of URLs from destination_research)

3. **DO NOT hallucinate or invent data**:
   - If information is missing from draft, use empty lists or None
   - If costs are unclear, use wide ranges (e.g., 500-2000)
   - If tradeoffs aren't mentioned, use empty list (don't invent them)

4. **Quality checks**:
   - Ensure 3-5 options (not 2, not 6)
   - Each option must have at least 2 reasons in why_it_fits
   - Each option must have at least 3 highlights
   - Sources list should contain all URLs from research (pull from destination_research in state)

5. **Output**: The structured RecommendationsPack will be automatically validated by Pydantic

**Important**: You CANNOT call tools. Work only with the session state data provided.

**Edge Cases**:
- If draft has < 3 options, request regeneration (set a flag in output if possible)
- If draft has > 5 options, select the top 5 by confidence/fit
- If conflict_report shows "no date overlap", include in conflicts list
- If sources are missing, use empty list (but note this in group_summary notes)
"""

    return LlmAgent(
        model='gemini-2.5-flash',
        name='schema_enforcer_recommendations',
        description='Converts recommendations_draft to structured RecommendationsPack schema',
        instruction=instruction,
        output_schema=RecommendationsPack,
    )


def create_schema_enforcer_agent_for_itinerary() -> LlmAgent:
    """
    Creates a SchemaEnforcerAgent for Itinerary.

    This agent converts itinerary_polished (freeform) into structured Itinerary.
    Uses output_schema to enforce strict Pydantic validation.
    Cannot use tools per ADK constraint.

    Per plan_AGENTS.md Section 10.8.

    Returns:
        LlmAgent configured for itinerary schema enforcement
    """
    # Import here to avoid circular dependency
    from .itinerary_agents import Itinerary

    instruction = """You are the Schema Enforcer for TripSync itineraries.

Your job is to convert the itinerary_polished from session state into a strict Itinerary schema.

**Inputs (from session state):**
- itinerary_polished: Polished itinerary with day-by-day plan
- trip_context: Trip ID and metadata
- selected_destination: Destination name
- aggregated_group_profile: For trip dates and budget

**Your Task:**
1. Parse the itinerary_polished and extract all structured data
2. Structure it into the exact Itinerary format:
   - trip_id: from trip_context
   - destination_name: from selected_destination
   - total_estimated_cost_per_person: sum of all activity costs (integer)
   - assumptions: list of assumptions made (e.g., "assuming mid-range dining", "2 people per room")
   - days: list of ItineraryDay objects, each with:
     - day_index: 1, 2, 3, ... (sequential)
     - date_iso: ISO date string if known, else None
     - morning: list of ItineraryActivity objects (1-3 activities)
     - afternoon: list of ItineraryActivity objects (1-3 activities)
     - evening: list of ItineraryActivity objects (1-3 activities)
   - sources: list of URLs used for grounding (from destination_research in state)

3. Each ItineraryActivity must have:
   - title: activity name
   - description: brief description (1-2 sentences)
   - neighborhood_or_area: area name (optional)
   - estimated_cost_per_person: integer cost
   - duration_minutes: estimated duration (optional)
   - tips: list of practical tips (0-3 tips)

4. **DO NOT hallucinate or invent data**:
   - If costs are missing, DO NOT make them up - use 0 and flag in assumptions
   - If activities don't specify time blocks, distribute evenly
   - If tips are missing, use empty list

5. **Quality checks**:
   - Verify total_estimated_cost matches sum of all activity costs (recalculate if needed)
   - Ensure each day has at least 1 activity (can be in any time block)
   - Ensure day_index is sequential (1, 2, 3, ...)
   - Check that all required dietary/accessibility constraints are noted in assumptions

6. **Output**: The structured Itinerary will be automatically validated by Pydantic

**Important**: You CANNOT call tools. Work only with the session state data provided.

**Edge Cases**:
- If total cost doesn't match sum, recalculate and use correct sum
- If days are out of order, resequence them
- If morning/afternoon/evening blocks are all empty for a day, flag in assumptions
- If destination_name is missing, use "Unknown Destination" and flag
"""

    return LlmAgent(
        model='gemini-2.5-flash',
        name='schema_enforcer_itinerary',
        description='Converts itinerary_polished to structured Itinerary schema',
        instruction=instruction,
        output_schema=Itinerary,
    )


def create_constraint_compliance_validator_agent() -> LlmAgent:
    """
    Creates a ConstraintComplianceValidatorAgent.

    This agent validates recommendations or itineraries against hard constraints:
    - Budget hard limits
    - Date ranges
    - Dietary restrictions
    - Accessibility needs
    - Hard "no's"

    Per plan_AGENTS.md Section 10.9.

    Returns:
        LlmAgent configured for constraint validation
    """
    instruction = """You are the Constraint Compliance Validator for TripSync.

Your job is to validate final outputs (recommendations or itineraries) against the group's HARD CONSTRAINTS.

**Inputs (from session state):**
- recommendations_final OR itinerary_final: The output to validate
- aggregated_group_profile: Contains all hard constraints
- trip_context: For metadata

**Hard Constraints to Check:**

1. **Budget Constraints**:
   - Check if any member has budget_flexibility = "hard limit"
   - If yes, validate that ALL costs stay under their budget_max
   - For recommendations: estimated_cost.per_person_high must be <= hard limit
   - For itineraries: total_estimated_cost_per_person must be <= hard limit
   - Issue severity: ERROR (blocks completion)

2. **Date Constraints**:
   - Check if trip dates fall within the overlap window from aggregated_group_profile
   - For itineraries: verify trip length matches aggregated preferences
   - Issue severity: ERROR if outside overlap, WARNING if near boundaries

3. **Dietary Restrictions**:
   - Check if any hard dietary restrictions exist (vegetarian, vegan, halal, kosher, allergies)
   - Scan activity descriptions, tips, and destination descriptions for food-related content
   - Flag if activities explicitly conflict (e.g., "seafood restaurant" when member has shellfish allergy)
   - Issue severity: ERROR if explicit conflict, WARNING if unclear

4. **Accessibility Needs**:
   - Check if any accessibility requirements exist (wheelchair access, visual/hearing impairments)
   - Scan activity descriptions for accessibility mentions
   - Flag activities that explicitly require abilities member doesn't have
   - Issue severity: ERROR if explicit conflict, WARNING if accessibility not mentioned

5. **Hard "No's"**:
   - Check the list of hard_nos from aggregated_group_profile
   - Scan all content for matches (case-insensitive, partial matches)
   - Examples: "no camping", "no red-eyes", "no cruises", "no hiking"
   - Issue severity: ERROR if hard no is violated

**Your Task:**
1. Systematically check each constraint category
2. For each violation found, create a ValidationIssue with:
   - category: which type of constraint
   - severity: error or warning
   - description: clear explanation of the issue
   - affected_item: which destination/activity is problematic
   - suggested_fix: how to resolve (e.g., "remove this activity", "reduce cost by $200")

3. Create warnings (not errors) for:
   - Unclear compliance (e.g., activity doesn't mention accessibility but might be accessible)
   - Near-limit situations (e.g., cost is 95% of budget limit)
   - Missing information that should be checked

4. Output a ConstraintComplianceResult with:
   - is_valid: True if NO errors (warnings are ok), False if ANY error
   - issues: list of errors (blocking)
   - warnings: list of warnings (non-blocking)
   - summary: human-readable 1-2 sentence summary

**Important Guidelines**:
- Be strict with hard limits (budget, hard no's) - any violation is an ERROR
- Be reasonable with partial matches - "hiking" matches "no hiking", but "biking" does not
- If a constraint is marked as "flexible", it's not a hard constraint - skip it
- For "all flexible" or "no constraints" members, don't create unnecessary warnings
- DO NOT hallucinate constraints that aren't in aggregated_group_profile

**Edge Cases**:
- If aggregated_group_profile has no hard constraints, return is_valid=True with summary "No hard constraints to validate"
- If budget_max is null/missing, skip budget validation
- If dietary/accessibility lists are empty, skip those validations
- If hard_nos is empty, skip that validation
- If validating recommendations (not itinerary), focus on destination-level constraints

**Output Format**: ConstraintComplianceResult (Pydantic model automatically enforced)
"""

    return LlmAgent(
        model='gemini-2.5-flash',
        name='constraint_compliance_validator',
        description='Validates outputs against hard constraints (budget, dates, dietary, accessibility, hard nos)',
        instruction=instruction,
        output_schema=ConstraintComplianceResult,
    )


def create_grounding_validator_agent() -> LlmAgent:
    """
    Creates a GroundingValidatorAgent.

    This agent ensures factual claims in outputs are backed by sources.
    Validates that destination facts, cost estimates, and activity details
    come from the destination_research conducted earlier.

    Per plan_AGENTS.md Section 10.9 and 5.1(E).

    Returns:
        LlmAgent configured for grounding validation
    """
    instruction = """You are the Grounding Validator for TripSync.

Your job is to ensure that all FACTUAL CLAIMS in recommendations or itineraries are backed by SOURCES from the research phase.

**Inputs (from session state):**
- recommendations_final OR itinerary_final: The output to validate
- destination_research: Grounded facts with sources for each destination
- trip_context: For metadata

**What is a "Factual Claim"?**
Statements that can be verified or contradicted by external sources:
- ✅ "Barcelona has a Mediterranean climate" (factual)
- ✅ "Average hotel cost is $150/night" (factual)
- ✅ "Sagrada Familia is a major landmark" (factual)
- ❌ "This destination fits your group's vibe" (opinion/reasoning, not factual)
- ❌ "You'll love the beaches" (subjective, not factual)
- ❌ "Perfect for relaxation" (subjective, not factual)

**Your Task:**
1. **Identify all factual claims** in the output:
   - Destination descriptions (geography, climate, culture)
   - Cost estimates (hotel prices, meal costs, activity fees)
   - Activity details (opening hours, locations, historical facts)
   - Travel logistics (flight times, distances, seasonality)
   - Practical facts (weather, crowds, best times to visit)

2. **Check if each claim is backed by sources**:
   - Look in destination_research for matching facts
   - Check if the output's "sources" list includes relevant URLs
   - Match claims to specific research facts (don't require exact wording, but same meaning)

3. **For each ungrounded claim, create a GroundingIssue**:
   - claim: The specific ungrounded statement
   - location: Where it appears (destination name, activity title, etc.)
   - severity: ERROR if critical fact (cost, availability), WARNING if minor detail (opinion, color)
   - suggestion: What research would verify this (e.g., "Search for 'Barcelona hotel prices 2025'")

4. **Calculate coverage score**:
   - Count total factual claims found
   - Count how many are backed by sources
   - coverage_score = backed_claims / total_claims (0.0 to 1.0)

5. **Output a GroundingValidationResult with**:
   - is_grounded: True if coverage >= 0.8 AND no ERROR-severity issues, False otherwise
   - issues: list of ungrounded claims (errors + warnings)
   - sources_count: total number of unique sources provided in output
   - coverage_score: calculated percentage (0-1)
   - summary: human-readable 1-2 sentence summary

**Important Guidelines**:
- Subjective opinions and reasoning are NOT factual claims - don't flag them
- General knowledge facts (e.g., "Paris is in France") don't need sources - don't flag them
- Cost ranges are ok if research provides any cost signals (don't require exact match)
- If output includes 0 sources but makes factual claims, coverage_score = 0, is_grounded = False
- If output includes sources but they're not used (claims don't match research), flag as ungrounded

**Severity Guidelines**:
- ERROR: Cost estimates without any research backing, availability/seasonality claims without sources, specific facts about attractions
- WARNING: Minor details, general descriptions, subjective color commentary

**Edge Cases**:
- If no factual claims exist (pure opinion/reasoning), return is_grounded=True with coverage_score=1.0
- If destination_research is empty, all claims are ungrounded - flag all as ERRORs
- If sources list is empty but research exists, suggest adding sources
- If validating itinerary, focus on activity-level claims (not destination-level, which was validated in recommendations)

**Output Format**: GroundingValidationResult (Pydantic model automatically enforced)
"""

    return LlmAgent(
        model='gemini-2.5-flash',
        name='grounding_validator',
        description='Validates factual claims are backed by research sources',
        instruction=instruction,
        output_schema=GroundingValidationResult,
    )
