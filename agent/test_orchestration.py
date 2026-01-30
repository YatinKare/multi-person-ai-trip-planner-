"""
Unit tests for TripSync orchestration agents.
Tests the router, regeneration loop, and session state management.
"""

import pytest
from datetime import datetime, timezone
from tripsync.orchestration import (
    create_router_agent,
    create_regeneration_loop_agent,
    create_recommendation_workflow,
    create_itinerary_workflow,
    SessionStateKeys,
    RouterDecision,
    ProgressEvent,
    add_progress_event,
    initialize_session_state,
)


# ============================================================================
# Test Agent Creation
# ============================================================================

def test_create_router_agent():
    """Test that router agent is created successfully."""
    agent = create_router_agent()

    assert agent is not None
    assert agent.name == 'tripsync_router'
    assert agent.model == 'gemini-2.5-flash'
    assert 'routes' in agent.description.lower() or 'router' in agent.description.lower()
    assert len(agent.instruction) > 0
    assert 'recommendations' in agent.instruction
    assert 'itinerary' in agent.instruction
    assert 'regenerate' in agent.instruction


def test_create_regeneration_loop_agent():
    """Test that regeneration loop agent is created successfully."""
    agent = create_regeneration_loop_agent(max_iterations=5)

    assert agent is not None
    assert agent.name == 'regeneration_loop'
    assert 'regeneration' in agent.description.lower()


def test_create_recommendation_workflow():
    """Test that recommendation workflow is created successfully."""
    workflow = create_recommendation_workflow()

    assert workflow is not None
    assert workflow.name == 'recommendation_workflow'
    assert 'recommendation' in workflow.description.lower()


def test_create_itinerary_workflow():
    """Test that itinerary workflow is created successfully."""
    workflow = create_itinerary_workflow()

    assert workflow is not None
    assert workflow.name == 'itinerary_workflow'
    assert 'itinerary' in workflow.description.lower()


# ============================================================================
# Test Session State Keys
# ============================================================================

def test_session_state_keys():
    """Test that all session state keys are defined."""
    # Input data keys
    assert hasattr(SessionStateKeys, 'TRIP_CONTEXT')
    assert hasattr(SessionStateKeys, 'RAW_PREFERENCES')
    assert hasattr(SessionStateKeys, 'SELECTED_DESTINATION')
    assert hasattr(SessionStateKeys, 'FEEDBACK_ITEMS')

    # Processed data keys
    assert hasattr(SessionStateKeys, 'NORMALIZED_PREFERENCES')
    assert hasattr(SessionStateKeys, 'AGGREGATED_GROUP_PROFILE')

    # Analysis keys
    assert hasattr(SessionStateKeys, 'CONFLICT_REPORT')

    # Recommendation pipeline keys
    assert hasattr(SessionStateKeys, 'CANDIDATE_DESTINATIONS')
    assert hasattr(SessionStateKeys, 'DESTINATION_RESEARCH')
    assert hasattr(SessionStateKeys, 'RECOMMENDATIONS_DRAFT')
    assert hasattr(SessionStateKeys, 'RECOMMENDATIONS_FINAL')

    # Itinerary pipeline keys
    assert hasattr(SessionStateKeys, 'ITINERARY_DRAFT')
    assert hasattr(SessionStateKeys, 'ITINERARY_FINAL')

    # Control flow keys
    assert hasattr(SessionStateKeys, 'REGEN_COUNT')
    assert hasattr(SessionStateKeys, 'MAX_REGEN_ITERATIONS')
    assert hasattr(SessionStateKeys, 'PROGRESS_EVENTS')
    assert hasattr(SessionStateKeys, 'ROUTER_ACTION')
    assert hasattr(SessionStateKeys, 'VALIDATION_RESULT')


# ============================================================================
# Test Data Models
# ============================================================================

def test_router_decision_model():
    """Test RouterDecision pydantic model."""
    decision = RouterDecision(
        action='recommendations',
        reason='Trip has preferences ready',
        missing_inputs=[],
        ready_to_proceed=True
    )

    assert decision.action == 'recommendations'
    assert decision.reason == 'Trip has preferences ready'
    assert decision.missing_inputs == []
    assert decision.ready_to_proceed is True


def test_router_decision_with_missing_inputs():
    """Test RouterDecision with missing inputs."""
    decision = RouterDecision(
        action='error',
        reason='Cannot generate itinerary without destination',
        missing_inputs=['selected_destination'],
        ready_to_proceed=False
    )

    assert decision.action == 'error'
    assert len(decision.missing_inputs) == 1
    assert 'selected_destination' in decision.missing_inputs
    assert decision.ready_to_proceed is False


def test_progress_event_model():
    """Test ProgressEvent pydantic model."""
    event = ProgressEvent(
        stage='preference_normalization',
        message='Normalizing member preferences...',
        timestamp=datetime.now(timezone.utc).isoformat(),
        metadata={'member_count': 3}
    )

    assert event.stage == 'preference_normalization'
    assert event.message == 'Normalizing member preferences...'
    assert event.metadata['member_count'] == 3
    assert len(event.timestamp) > 0


# ============================================================================
# Test Session State Initialization
# ============================================================================

def test_initialize_session_state_minimal():
    """Test session state initialization with minimal inputs."""
    trip_id = 'test-trip-123'
    raw_preferences = [
        {
            'user_id': 'user-1',
            'dates': {'earliest_start': '2025-05-01', 'latest_end': '2025-05-10'},
            'budget': {'min_budget': 500, 'max_budget': 1500}
        }
    ]

    state = initialize_session_state(trip_id, raw_preferences)

    assert SessionStateKeys.TRIP_CONTEXT in state
    assert state[SessionStateKeys.TRIP_CONTEXT]['trip_id'] == trip_id
    assert SessionStateKeys.RAW_PREFERENCES in state
    assert len(state[SessionStateKeys.RAW_PREFERENCES]) == 1
    assert state[SessionStateKeys.REGEN_COUNT] == 0
    assert state[SessionStateKeys.MAX_REGEN_ITERATIONS] == 5
    assert state[SessionStateKeys.PROGRESS_EVENTS] == []


def test_initialize_session_state_full():
    """Test session state initialization with all inputs."""
    trip_id = 'test-trip-456'
    raw_preferences = [
        {'user_id': 'user-1', 'vibes': ['beach', 'relaxation']},
        {'user_id': 'user-2', 'vibes': ['city', 'culture']}
    ]
    trip_context = {
        'trip_id': trip_id,
        'name': 'Summer Trip 2025',
        'status': 'collecting',
        'member_count': 2
    }
    selected_destination = {
        'name': 'Lisbon',
        'region': 'Portugal',
        'estimated_cost': 1200
    }
    feedback_items = [
        {'activity_id': 'act-1', 'feedback': 'too expensive'},
        {'activity_id': 'act-2', 'feedback': 'not accessible'}
    ]

    state = initialize_session_state(
        trip_id=trip_id,
        raw_preferences=raw_preferences,
        trip_context=trip_context,
        selected_destination=selected_destination,
        feedback_items=feedback_items,
        max_regen_iterations=3
    )

    assert state[SessionStateKeys.TRIP_CONTEXT] == trip_context
    assert len(state[SessionStateKeys.RAW_PREFERENCES]) == 2
    assert SessionStateKeys.SELECTED_DESTINATION in state
    assert state[SessionStateKeys.SELECTED_DESTINATION]['name'] == 'Lisbon'
    assert SessionStateKeys.FEEDBACK_ITEMS in state
    assert len(state[SessionStateKeys.FEEDBACK_ITEMS]) == 2
    assert state[SessionStateKeys.MAX_REGEN_ITERATIONS] == 3


# ============================================================================
# Test Progress Event Helper
# ============================================================================

def test_add_progress_event():
    """Test adding progress events to session state."""
    events = []

    # Add first event
    events = add_progress_event(
        events=events,
        stage='initialization',
        message='Loading trip data...',
        metadata={'trip_id': 'test-123'}
    )

    assert len(events) == 1
    assert events[0].stage == 'initialization'
    assert events[0].message == 'Loading trip data...'
    assert events[0].metadata['trip_id'] == 'test-123'

    # Add second event
    events = add_progress_event(
        events=events,
        stage='preference_normalization',
        message='Normalizing 3 member preferences...'
    )

    assert len(events) == 2
    assert events[1].stage == 'preference_normalization'
    assert events[1].metadata == {}


# ============================================================================
# Test Custom Max Iterations
# ============================================================================

def test_regeneration_loop_custom_iterations():
    """Test regeneration loop with custom max iterations."""
    agent = create_regeneration_loop_agent(max_iterations=10)

    assert agent is not None
    assert '10' in agent.description


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
