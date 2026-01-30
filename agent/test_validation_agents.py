"""
Unit tests for validation_agents.py

Tests for SchemaEnforcerAgent, ConstraintComplianceValidatorAgent, and GroundingValidatorAgent.
"""

import pytest
from tripsync.validation_agents import (
    create_schema_enforcer_agent_for_recommendations,
    create_schema_enforcer_agent_for_itinerary,
    create_constraint_compliance_validator_agent,
    create_grounding_validator_agent,
    ValidationIssue,
    ConstraintComplianceResult,
    GroundingIssue,
    GroundingValidationResult,
)


# ============================================================================
# Agent Creation Tests
# ============================================================================


def test_create_schema_enforcer_agent_for_recommendations():
    """Test creation of schema enforcer agent for recommendations."""
    agent = create_schema_enforcer_agent_for_recommendations()

    assert agent is not None
    assert agent.name == 'schema_enforcer_recommendations'
    assert 'SchemaEnforcerAgent' in agent.description or 'schema' in agent.description.lower()
    assert agent.model == 'gemini-2.5-flash'
    # Verify output_schema is set (this is critical for schema enforcement)
    assert hasattr(agent, 'output_schema')


def test_create_schema_enforcer_agent_for_itinerary():
    """Test creation of schema enforcer agent for itinerary."""
    agent = create_schema_enforcer_agent_for_itinerary()

    assert agent is not None
    assert agent.name == 'schema_enforcer_itinerary'
    assert 'schema' in agent.description.lower()
    assert agent.model == 'gemini-2.5-flash'
    # Verify output_schema is set
    assert hasattr(agent, 'output_schema')


def test_create_constraint_compliance_validator_agent():
    """Test creation of constraint compliance validator agent."""
    agent = create_constraint_compliance_validator_agent()

    assert agent is not None
    assert agent.name == 'constraint_compliance_validator'
    assert 'constraint' in agent.description.lower() or 'compliance' in agent.description.lower()
    assert agent.model == 'gemini-2.5-flash'
    # Verify output_schema is set
    assert hasattr(agent, 'output_schema')


def test_create_grounding_validator_agent():
    """Test creation of grounding validator agent."""
    agent = create_grounding_validator_agent()

    assert agent is not None
    assert agent.name == 'grounding_validator'
    assert 'grounding' in agent.description.lower() or 'factual' in agent.description.lower()
    assert agent.model == 'gemini-2.5-flash'
    # Verify output_schema is set
    assert hasattr(agent, 'output_schema')


# ============================================================================
# ValidationIssue Model Tests
# ============================================================================


def test_validation_issue_full():
    """Test ValidationIssue with all fields."""
    issue = ValidationIssue(
        category="budget",
        severity="error",
        description="Total cost exceeds hard budget limit",
        affected_item="Day 3 lunch activity",
        suggested_fix="Reduce activity cost by $50 or remove this activity"
    )

    assert issue.category == "budget"
    assert issue.severity == "error"
    assert issue.description == "Total cost exceeds hard budget limit"
    assert issue.affected_item == "Day 3 lunch activity"
    assert issue.suggested_fix == "Reduce activity cost by $50 or remove this activity"


def test_validation_issue_minimal():
    """Test ValidationIssue with only required fields."""
    issue = ValidationIssue(
        category="dietary",
        severity="warning",
        description="Activity may not accommodate vegan dietary restriction"
    )

    assert issue.category == "dietary"
    assert issue.severity == "warning"
    assert issue.description == "Activity may not accommodate vegan dietary restriction"
    assert issue.affected_item is None
    assert issue.suggested_fix is None


def test_validation_issue_all_categories():
    """Test ValidationIssue accepts all valid categories."""
    categories = ["budget", "dates", "dietary", "accessibility", "hard_no", "other"]

    for category in categories:
        issue = ValidationIssue(
            category=category,
            severity="error",
            description=f"Test {category} issue"
        )
        assert issue.category == category


def test_validation_issue_all_severities():
    """Test ValidationIssue accepts all valid severities."""
    severities = ["error", "warning"]

    for severity in severities:
        issue = ValidationIssue(
            category="budget",
            severity=severity,
            description=f"Test {severity} issue"
        )
        assert issue.severity == severity


# ============================================================================
# ConstraintComplianceResult Model Tests
# ============================================================================


def test_constraint_compliance_result_valid():
    """Test ConstraintComplianceResult with valid (passing) result."""
    result = ConstraintComplianceResult(
        is_valid=True,
        issues=[],
        warnings=[
            ValidationIssue(
                category="budget",
                severity="warning",
                description="Cost is 95% of budget limit"
            )
        ],
        summary="Validation passed with 1 warning"
    )

    assert result.is_valid is True
    assert len(result.issues) == 0
    assert len(result.warnings) == 1
    assert result.summary == "Validation passed with 1 warning"


def test_constraint_compliance_result_invalid():
    """Test ConstraintComplianceResult with invalid (failing) result."""
    result = ConstraintComplianceResult(
        is_valid=False,
        issues=[
            ValidationIssue(
                category="budget",
                severity="error",
                description="Total cost exceeds hard budget limit by $500"
            ),
            ValidationIssue(
                category="hard_no",
                severity="error",
                description="Activity includes 'camping' which is a hard no"
            )
        ],
        warnings=[],
        summary="Validation failed with 2 errors"
    )

    assert result.is_valid is False
    assert len(result.issues) == 2
    assert len(result.warnings) == 0
    assert "failed" in result.summary.lower()


def test_constraint_compliance_result_no_constraints():
    """Test ConstraintComplianceResult with no constraints to validate."""
    result = ConstraintComplianceResult(
        is_valid=True,
        issues=[],
        warnings=[],
        summary="No hard constraints to validate"
    )

    assert result.is_valid is True
    assert len(result.issues) == 0
    assert len(result.warnings) == 0


# ============================================================================
# GroundingIssue Model Tests
# ============================================================================


def test_grounding_issue_full():
    """Test GroundingIssue with all fields."""
    issue = GroundingIssue(
        claim="Average hotel cost is $200/night",
        location="Barcelona destination option",
        severity="error",
        suggestion="Search for 'Barcelona hotel prices 2025'"
    )

    assert issue.claim == "Average hotel cost is $200/night"
    assert issue.location == "Barcelona destination option"
    assert issue.severity == "error"
    assert issue.suggestion == "Search for 'Barcelona hotel prices 2025'"


def test_grounding_issue_minimal():
    """Test GroundingIssue with only required fields."""
    issue = GroundingIssue(
        claim="Sagrada Familia is the most visited monument",
        location="Day 2 morning activity",
        severity="warning"
    )

    assert issue.claim == "Sagrada Familia is the most visited monument"
    assert issue.location == "Day 2 morning activity"
    assert issue.severity == "warning"
    assert issue.suggestion is None


def test_grounding_issue_all_severities():
    """Test GroundingIssue accepts all valid severities."""
    severities = ["error", "warning"]

    for severity in severities:
        issue = GroundingIssue(
            claim="Test factual claim",
            location="Test location",
            severity=severity
        )
        assert issue.severity == severity


# ============================================================================
# GroundingValidationResult Model Tests
# ============================================================================


def test_grounding_validation_result_well_grounded():
    """Test GroundingValidationResult with well-grounded output."""
    result = GroundingValidationResult(
        is_grounded=True,
        issues=[],
        sources_count=12,
        coverage_score=0.95,
        summary="All factual claims are backed by sources"
    )

    assert result.is_grounded is True
    assert len(result.issues) == 0
    assert result.sources_count == 12
    assert result.coverage_score == 0.95


def test_grounding_validation_result_poorly_grounded():
    """Test GroundingValidationResult with poorly grounded output."""
    result = GroundingValidationResult(
        is_grounded=False,
        issues=[
            GroundingIssue(
                claim="Average cost is $150/day",
                location="Tokyo destination",
                severity="error",
                suggestion="Search for 'Tokyo travel costs 2025'"
            ),
            GroundingIssue(
                claim="Best season is spring",
                location="Tokyo destination",
                severity="warning"
            )
        ],
        sources_count=2,
        coverage_score=0.4,
        summary="Only 40% of factual claims are backed by sources"
    )

    assert result.is_grounded is False
    assert len(result.issues) == 2
    assert result.sources_count == 2
    assert result.coverage_score == 0.4


def test_grounding_validation_result_no_sources():
    """Test GroundingValidationResult with no sources provided."""
    result = GroundingValidationResult(
        is_grounded=False,
        issues=[
            GroundingIssue(
                claim="Ungrounded cost estimate",
                location="Destination option 1",
                severity="error"
            )
        ],
        sources_count=0,
        coverage_score=0.0,
        summary="No sources provided for factual claims"
    )

    assert result.is_grounded is False
    assert result.sources_count == 0
    assert result.coverage_score == 0.0


def test_grounding_validation_result_coverage_score_bounds():
    """Test GroundingValidationResult coverage_score is bounded 0-1."""
    # Valid at boundaries
    result_zero = GroundingValidationResult(
        is_grounded=False,
        issues=[],
        sources_count=0,
        coverage_score=0.0,
        summary="Test"
    )
    assert result_zero.coverage_score == 0.0

    result_one = GroundingValidationResult(
        is_grounded=True,
        issues=[],
        sources_count=10,
        coverage_score=1.0,
        summary="Test"
    )
    assert result_one.coverage_score == 1.0

    # Invalid: should raise validation error
    with pytest.raises(Exception):  # Pydantic validation error
        GroundingValidationResult(
            is_grounded=False,
            issues=[],
            sources_count=0,
            coverage_score=-0.1,  # Invalid: below 0
            summary="Test"
        )

    with pytest.raises(Exception):  # Pydantic validation error
        GroundingValidationResult(
            is_grounded=False,
            issues=[],
            sources_count=0,
            coverage_score=1.5,  # Invalid: above 1
            summary="Test"
        )


# ============================================================================
# Integration Tests
# ============================================================================


def test_all_validation_agents_created():
    """Test that all validation agents can be created without errors."""
    agents = [
        create_schema_enforcer_agent_for_recommendations(),
        create_schema_enforcer_agent_for_itinerary(),
        create_constraint_compliance_validator_agent(),
        create_grounding_validator_agent(),
    ]

    assert len(agents) == 4
    assert all(agent is not None for agent in agents)
    assert all(hasattr(agent, 'name') for agent in agents)
    assert all(hasattr(agent, 'model') for agent in agents)


def test_all_validation_models_work_together():
    """Test that all validation models can be used together."""
    # Create sample validation issues
    validation_issue = ValidationIssue(
        category="budget",
        severity="error",
        description="Cost exceeds limit"
    )

    grounding_issue = GroundingIssue(
        claim="Sample factual claim",
        location="Sample location",
        severity="warning"
    )

    # Create sample results using the issues
    compliance_result = ConstraintComplianceResult(
        is_valid=False,
        issues=[validation_issue],
        warnings=[],
        summary="Validation failed"
    )

    grounding_result = GroundingValidationResult(
        is_grounded=False,
        issues=[grounding_issue],
        sources_count=5,
        coverage_score=0.6,
        summary="Partial grounding"
    )

    # Verify everything works together
    assert compliance_result.is_valid is False
    assert grounding_result.is_grounded is False
    assert len(compliance_result.issues) == 1
    assert len(grounding_result.issues) == 1


def test_validation_workflow_integration():
    """Test that validation agents fit into the workflow pattern."""
    # This tests the pattern used in orchestration.py
    from tripsync.validation_agents import (
        create_schema_enforcer_agent_for_recommendations,
        create_constraint_compliance_validator_agent,
        create_grounding_validator_agent,
    )

    # Create agents in the order they'd be used in workflow
    schema_enforcer = create_schema_enforcer_agent_for_recommendations()
    constraint_validator = create_constraint_compliance_validator_agent()
    grounding_validator = create_grounding_validator_agent()

    # Verify they can be organized in a pipeline
    validation_pipeline = [schema_enforcer, constraint_validator, grounding_validator]
    assert len(validation_pipeline) == 3

    # Verify each agent has the required properties for ADK workflow
    for agent in validation_pipeline:
        assert hasattr(agent, 'name')
        assert hasattr(agent, 'model')
        assert hasattr(agent, 'description')
        assert hasattr(agent, 'instruction')
        assert hasattr(agent, 'output_schema')
