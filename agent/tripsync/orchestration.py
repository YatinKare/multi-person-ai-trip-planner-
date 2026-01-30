"""
Orchestration agents for TripSync.
Handles routing, workflow coordination, and regeneration loops.
"""

from google.adk.agents import Agent, SequentialAgent, LoopAgent
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

# ============================================================================
# Session State Keys (Canonical)
# ============================================================================
class SessionStateKeys:
    """Canonical keys for session state to avoid collisions."""

    # Input data
    TRIP_CONTEXT = "trip_context"
    RAW_PREFERENCES = "raw_preferences"
    SELECTED_DESTINATION = "selected_destination"
    FEEDBACK_ITEMS = "feedback_items"

    # Normalized/processed data
    NORMALIZED_PREFERENCES = "normalized_preferences"
    AGGREGATED_GROUP_PROFILE = "aggregated_group_profile"

    # Analysis outputs
    CONFLICT_REPORT = "conflict_report"

    # Destination recommendation pipeline
    CANDIDATE_DESTINATIONS = "candidate_destinations"
    DESTINATION_RESEARCH = "destination_research"
    RECOMMENDATIONS_DRAFT = "recommendations_draft"
    RECOMMENDATIONS_FINAL = "recommendations_final"

    # Itinerary pipeline
    ITINERARY_DRAFT = "itinerary_draft"
    ITINERARY_FINAL = "itinerary_final"

    # Control flow
    REGEN_COUNT = "regen_count"
    MAX_REGEN_ITERATIONS = "max_regen_iterations"
    PROGRESS_EVENTS = "progress_events"
    ROUTER_ACTION = "router_action"
    VALIDATION_RESULT = "validation_result"


# ============================================================================
# Data Models for Session State
# ============================================================================
class RouterDecision(BaseModel):
    """Router's decision on which workflow to execute."""
    action: str = Field(
        description="Action to take: 'recommendations', 'itinerary', 'regenerate', 'conflicts_only', 'explain', 'error'"
    )
    reason: str = Field(description="Explanation for the routing decision")
    missing_inputs: list[str] = Field(
        default_factory=list,
        description="List of missing required inputs"
    )
    ready_to_proceed: bool = Field(
        default=True,
        description="Whether the workflow can proceed"
    )


class ProgressEvent(BaseModel):
    """Progress event for long-running operations."""
    stage: str = Field(description="Current stage name")
    message: str = Field(description="Human-readable progress message")
    timestamp: str = Field(description="ISO timestamp")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


# ============================================================================
# TripSyncRouterAgent - Main orchestration router
# ============================================================================

ROUTER_INSTRUCTION = """You are the TripSync router agent. Your job is to analyze the user's action and trip state,
then decide which workflow should run next.

**Available Actions:**
- `recommendations`: Generate 3-5 destination options based on aggregated preferences
- `itinerary`: Generate day-by-day itinerary for a selected destination
- `regenerate`: Regenerate itinerary based on user feedback (bounded iterations)
- `conflicts_only`: Analyze preference conflicts without generating recommendations
- `explain`: Provide information about the trip state or constraints

**Decision Logic:**

1. **For 'recommendations' request:**
   - Required inputs: raw_preferences (at least 1 member's preferences)
   - Optional: aggregated_group_profile, conflict_report
   - If missing preferences: action='error', set missing_inputs=['preferences']
   - If ready: action='recommendations'

2. **For 'itinerary' request:**
   - Required inputs: selected_destination, aggregated_group_profile
   - If selected_destination is missing: action='error', set missing_inputs=['destination']
   - If aggregated_group_profile is missing: action='error', set missing_inputs=['preferences']
   - If ready: action='itinerary'

3. **For 'regenerate' request:**
   - Required inputs: existing itinerary_final, feedback_items
   - Check regen_count: if >= max_regen_iterations, action='error', reason='Max regeneration limit reached'
   - If ready: action='regenerate'

4. **For 'conflicts_only' or 'explain':**
   - These can run with whatever data is available
   - Always set ready_to_proceed=True

**Important Rules:**
- NEVER fabricate trip facts - if data is missing, request it via missing_inputs
- Always explain your routing decision clearly
- If multiple inputs are missing, list all of them
- Set ready_to_proceed=False if critical inputs are missing

**Output Format:**
Respond with a JSON object containing:
- action: one of the available actions
- reason: clear explanation of why this action was chosen
- missing_inputs: array of missing required inputs (empty if none)
- ready_to_proceed: boolean indicating if workflow can start

Example outputs:

{
  "action": "recommendations",
  "reason": "Trip has 3 member preferences submitted and no existing recommendations. Ready to generate destination options.",
  "missing_inputs": [],
  "ready_to_proceed": true
}

{
  "action": "error",
  "reason": "Cannot generate itinerary without a selected destination. Organizer must first choose from recommendations.",
  "missing_inputs": ["selected_destination"],
  "ready_to_proceed": false
}

{
  "action": "regenerate",
  "reason": "Organizer provided feedback on 2 activities. Regeneration count is 1/5, proceeding with iteration.",
  "missing_inputs": [],
  "ready_to_proceed": true
}
"""


def create_router_agent() -> Agent:
    """
    Creates the TripSyncRouterAgent that routes user actions to appropriate workflows.

    This agent:
    - Reads from session state: trip_context, raw_preferences, selected_destination,
      feedback_items, regen_count, aggregated_group_profile
    - Writes routing decision to: router_action
    - Does NOT use tools (pure LLM reasoning)

    Returns:
        Agent configured as the router
    """
    return Agent(
        model='gemini-2.5-flash',
        name='tripsync_router',
        description='Routes user actions to appropriate TripSync workflows based on trip state and available data',
        instruction=ROUTER_INSTRUCTION,
        # Router reads state and makes decisions - no tools needed
        # Outputs will be written to session state via output_key or explicit writes
    )


# ============================================================================
# RegenerationLoopAgent - Bounded feedback iteration
# ============================================================================

REGENERATION_INSTRUCTION = """You are the TripSync regeneration coordinator. Your job is to manage the iterative
feedback loop for itinerary regeneration.

**Workflow:**
1. Read the current itinerary_draft from session state
2. Read the feedback_items from session state
3. Read the regen_count from session state
4. Check if regen_count >= max_regen_iterations (default: 5)
5. If limit reached, output a structured error and stop
6. Otherwise, incorporate feedback and regenerate itinerary
7. Increment regen_count
8. Validate the new itinerary
9. If validation passes, mark as complete
10. If validation fails and iterations remain, loop again

**Feedback Integration Rules:**
- Address each feedback_item explicitly
- If feedback conflicts with hard constraints, explain the tradeoff
- If feedback is impossible (e.g., "make it free"), suggest alternatives
- Track which feedback items were addressed vs. which couldn't be satisfied

**Stop Conditions:**
1. Validation passes (itinerary meets all constraints)
2. Max iterations reached
3. Feedback cannot be satisfied due to constraints (output explanation)

**Output Format:**
Update session state with:
- itinerary_draft: new version incorporating feedback
- regen_count: incremented count
- validation_result: pass/fail with details
- feedback_resolution: which items were addressed and how

If stopping due to limit or impossibility:
{
  "status": "stopped",
  "reason": "Max regeneration limit reached" OR "Cannot satisfy feedback due to constraints",
  "final_itinerary": <last valid version>,
  "unresolved_feedback": [<list of feedback items that couldn't be addressed>],
  "suggestions": [<alternative approaches>]
}
"""


def create_regeneration_loop_agent(max_iterations: int = 5) -> LoopAgent:
    """
    Creates a LoopAgent for bounded itinerary regeneration with feedback.

    This agent:
    - Loops up to max_iterations times
    - Reads: itinerary_draft, feedback_items, regen_count, aggregated_group_profile
    - Writes: itinerary_draft (updated), regen_count (incremented), validation_result
    - Stops when validation passes or max iterations reached

    Args:
        max_iterations: Maximum number of regeneration attempts (default: 5)

    Returns:
        LoopAgent configured for regeneration workflow
    """

    # Create the regeneration logic agent
    regeneration_agent = Agent(
        model='gemini-2.5-flash',
        name='regeneration_coordinator',
        description='Coordinates iterative itinerary regeneration based on user feedback',
        instruction=REGENERATION_INSTRUCTION,
    )

    # Wrap in LoopAgent with stop condition
    # The LoopAgent will execute the regeneration_agent repeatedly until:
    # 1. validation_result.pass == True (success)
    # 2. regen_count >= max_iterations (limit reached)
    loop_agent = LoopAgent(
        sub_agents=[regeneration_agent],
        name='regeneration_loop',
        description=f'Bounded regeneration loop (max {max_iterations} iterations)',
        max_iterations=max_iterations,
        # Stop condition will be checked via session state
        # ADK LoopAgent supports custom stop functions
    )

    return loop_agent


# ============================================================================
# Workflow Agents (RecommendationWorkflowAgent, ItineraryWorkflowAgent)
# ============================================================================

def create_recommendation_workflow() -> SequentialAgent:
    """
    Creates the RecommendationWorkflowAgent that orchestrates the full
    destination recommendation pipeline.

    Pipeline stages:
    1. PreferenceNormalizerAgent - normalize raw preferences (Task 3.2 ✓)
    2. AggregationAgent (function, not LLM) - compute aggregated group profile (Task 3.2 ✓)
    3. ConflictDetectorAgent - identify conflicts (Task 3.2 ✓)
    4. CandidateDestinationGeneratorAgent - generate 8-12 candidates (Task 3.3 ✓)
    5. DestinationResearchAgent - research candidates using Google Search (Task 3.3 ✓)
    6. DestinationRankerAgent - select top 3-5 with reasoning (Task 3.3 ✓)
    7. SchemaEnforcerAgent - convert to RecommendationsPack (Task 3.5, placeholder for now)
    8. ConstraintComplianceValidatorAgent - validate against constraints (Task 3.5, placeholder for now)
    9. GroundingValidatorAgent - ensure factual claims are backed (Task 3.5, placeholder for now)

    Per plan_AGENTS.md Section 9.2.

    Returns:
        SequentialAgent orchestrating the recommendation pipeline
    """
    # Import agents from preference_agents and recommendation_agents modules
    # These are imported here to avoid circular dependencies
    from .preference_agents import (
        create_preference_normalizer_agent,
        create_conflict_detector_agent,
    )
    from .recommendation_agents import (
        create_candidate_generator_agent,
        create_destination_research_agent,
        create_destination_ranker_agent,
    )

    # Note: AggregationAgent is a function, not an LLM agent, so it will need to be
    # called differently in the workflow. For now, we'll need to create a wrapper agent
    # that calls the aggregation function. This is a known pattern in ADK.

    # Create a simple aggregation wrapper agent
    aggregation_wrapper = Agent(
        model='gemini-2.5-flash',
        name='aggregation_wrapper',
        description='Wrapper that calls aggregate_preferences function',
        instruction="""
You are a wrapper agent for the AggregationAgent function.

Your job is to:
1. Read normalized_preferences from session state
2. Call the aggregate_preferences function (via a tool or direct invocation)
3. Write the result to aggregated_group_profile in session state

Note: The actual aggregation logic is deterministic and handled by computation tools.
You are just coordinating the data flow.

Read normalized_preferences, aggregate them using the computation tools, and write to aggregated_group_profile.
""",
    )

    # Validation agents are placeholders for Task 3.5
    schema_enforcer_placeholder = Agent(
        model='gemini-2.5-flash',
        name='schema_enforcer_placeholder',
        description='Placeholder for SchemaEnforcerAgent (Task 3.5)',
        instruction='Convert recommendations_draft to structured RecommendationsPack. Placeholder for Task 3.5.',
    )

    constraint_validator_placeholder = Agent(
        model='gemini-2.5-flash',
        name='constraint_validator_placeholder',
        description='Placeholder for ConstraintComplianceValidatorAgent (Task 3.5)',
        instruction='Validate recommendations against constraints. Placeholder for Task 3.5.',
    )

    grounding_validator_placeholder = Agent(
        model='gemini-2.5-flash',
        name='grounding_validator_placeholder',
        description='Placeholder for GroundingValidatorAgent (Task 3.5)',
        instruction='Validate grounding of recommendations. Placeholder for Task 3.5.',
    )

    # Create the sequential workflow
    # Per plan_AGENTS.md Section 9.2, this follows the sequence diagram
    workflow = SequentialAgent(
        sub_agents=[
            create_preference_normalizer_agent(),       # Step 1: Normalize
            aggregation_wrapper,                         # Step 2: Aggregate (wrapper for function)
            create_conflict_detector_agent(),            # Step 3: Detect conflicts
            create_candidate_generator_agent(),          # Step 4: Generate 8-12 candidates
            create_destination_research_agent(),         # Step 5: Research using Google Search
            create_destination_ranker_agent(),           # Step 6: Rank and select top 3-5
            schema_enforcer_placeholder,                 # Step 7: Schema enforcement (Task 3.5)
            constraint_validator_placeholder,            # Step 8: Constraint validation (Task 3.5)
            grounding_validator_placeholder,             # Step 9: Grounding validation (Task 3.5)
        ],
        name='recommendation_workflow',
        description='Orchestrates destination recommendation generation pipeline',
    )

    return workflow


def create_itinerary_workflow() -> SequentialAgent:
    """
    Creates the ItineraryWorkflowAgent that orchestrates the full
    itinerary generation pipeline.

    Pipeline stages:
    1. ItineraryDraftAgent - create day-by-day draft
    2. CostSanityAgent - validate costs and budget
    3. ItineraryPolishAgent - improve clarity and flow
    4. SchemaEnforcerAgent - convert to Itinerary schema
    5. ConstraintComplianceValidatorAgent - validate constraints
    6. GroundingValidatorAgent - validate factual claims

    Note: Individual agents will be implemented in separate tasks.
    This is a placeholder structure.

    Returns:
        SequentialAgent orchestrating the itinerary pipeline
    """
    # Placeholder - agents will be created in Tasks 3.4, 3.5
    # For now, return a sequential workflow with a placeholder

    placeholder_agent = Agent(
        model='gemini-2.5-flash',
        name='itinerary_workflow_placeholder',
        description='Placeholder for itinerary workflow (to be implemented in Task 3.4)',
        instruction='This is a placeholder. The full itinerary pipeline will be implemented in Task 3.4.',
    )

    workflow = SequentialAgent(
        sub_agents=[placeholder_agent],
        name='itinerary_workflow',
        description='Orchestrates itinerary generation pipeline',
    )

    return workflow


# ============================================================================
# Utility Functions
# ============================================================================

def add_progress_event(
    events: list[ProgressEvent],
    stage: str,
    message: str,
    metadata: Optional[Dict[str, Any]] = None
) -> list[ProgressEvent]:
    """
    Helper to add a progress event to the session state events list.

    Args:
        events: Current list of progress events
        stage: Stage name (e.g., 'preference_normalization', 'destination_research')
        message: Human-readable message
        metadata: Optional additional data

    Returns:
        Updated events list
    """
    from datetime import datetime, timezone

    event = ProgressEvent(
        stage=stage,
        message=message,
        timestamp=datetime.now(timezone.utc).isoformat(),
        metadata=metadata or {}
    )

    events.append(event)
    return events


def initialize_session_state(
    trip_id: str,
    raw_preferences: list[Dict[str, Any]],
    trip_context: Optional[Dict[str, Any]] = None,
    selected_destination: Optional[Dict[str, Any]] = None,
    feedback_items: Optional[list[Dict[str, Any]]] = None,
    max_regen_iterations: int = 5
) -> Dict[str, Any]:
    """
    Initialize session state with required data for agent workflows.

    Args:
        trip_id: Trip UUID
        raw_preferences: List of member preferences (from database)
        trip_context: Optional trip metadata (name, status, member_count)
        selected_destination: Optional selected destination (for itinerary generation)
        feedback_items: Optional feedback items (for regeneration)
        max_regen_iterations: Max regeneration attempts (default: 5)

    Returns:
        Dictionary of session state ready for ADK context
    """
    state = {
        SessionStateKeys.TRIP_CONTEXT: trip_context or {"trip_id": trip_id},
        SessionStateKeys.RAW_PREFERENCES: raw_preferences,
        SessionStateKeys.REGEN_COUNT: 0,
        SessionStateKeys.MAX_REGEN_ITERATIONS: max_regen_iterations,
        SessionStateKeys.PROGRESS_EVENTS: [],
    }

    if selected_destination:
        state[SessionStateKeys.SELECTED_DESTINATION] = selected_destination

    if feedback_items:
        state[SessionStateKeys.FEEDBACK_ITEMS] = feedback_items

    return state
