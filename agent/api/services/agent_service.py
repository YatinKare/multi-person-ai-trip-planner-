"""
Service layer for AI agent orchestration.

This module handles the integration between FastAPI endpoints and TripSync agents.
Coordinates workflow execution, session state management, and result storage.

Per plan_PROGRESS.md Task 3.6.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from tripsync.orchestration import (
    create_router_agent,
    create_recommendation_workflow,
    create_itinerary_workflow,
    create_regeneration_loop_agent,
    initialize_session_state,
    SessionStateKeys
)
from tripsync.data_access_tools import (
    load_trip_context,
    load_member_preferences,
    load_existing_recommendations,
    load_existing_itinerary,
    store_recommendations,
    store_itinerary,
    store_progress
)
from tripsync.preference_agents import aggregate_preferences

logger = logging.getLogger(__name__)


class AgentService:
    """Service for orchestrating TripSync AI agents."""

    def __init__(self):
        """Initialize the agent service."""
        pass

    async def generate_recommendations(
        self,
        trip_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Generate destination recommendations for a trip.

        Args:
            trip_id: UUID of the trip
            user_id: UUID of the user requesting recommendations

        Returns:
            dict: Recommendations result with destinations or error
        """
        try:
            logger.info(f"Generating recommendations for trip {trip_id}")

            # Load trip context and preferences
            trip_context = load_trip_context(trip_id)
            if "error" in trip_context:
                return {"success": False, "error": trip_context["error"]}

            raw_preferences = load_member_preferences(trip_id)
            if not raw_preferences:
                return {
                    "success": False,
                    "error": "No preferences found. Members must submit preferences first."
                }

            # Check for errors in preferences
            if len(raw_preferences) == 1 and "error" in raw_preferences[0]:
                return {"success": False, "error": raw_preferences[0]["error"]}

            # Aggregate preferences using deterministic function
            aggregated_profile = aggregate_preferences(raw_preferences)

            # Initialize session state
            session_state = initialize_session_state(
                trip_context=trip_context,
                raw_preferences=raw_preferences,
                aggregated_group_profile=aggregated_profile
            )

            # Create and run recommendation workflow
            store_progress(trip_id, "Starting destination recommendation generation", "initialization")
            workflow_agent = create_recommendation_workflow()

            # Run the workflow
            workflow_result = await workflow_agent.run(
                user_input="Generate destination recommendations for this trip",
                session_state=session_state
            )

            # Extract recommendations from session state
            recommendations_final = session_state.get(SessionStateKeys.RECOMMENDATIONS_FINAL)

            if not recommendations_final:
                return {
                    "success": False,
                    "error": "Recommendation generation failed to produce output"
                }

            # Store recommendations in database
            recommendations_payload = {
                "options": recommendations_final.get("options", []),
                "generated_by": user_id,
                "group_summary": recommendations_final.get("group_summary", ""),
                "conflicts": recommendations_final.get("conflicts", [])
            }

            store_result = store_recommendations(trip_id, recommendations_payload)

            if not store_result.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to save recommendations: {store_result.get('error')}"
                }

            store_progress(trip_id, "Recommendations generated successfully", "complete")

            return {
                "success": True,
                "recommendations": recommendations_final,
                "recommendation_id": store_result.get("recommendation_id"),
                "generated_at": store_result.get("generated_at")
            }

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Recommendation generation failed: {str(e)}"
            }

    async def generate_itinerary(
        self,
        trip_id: str,
        destination_name: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Generate a full itinerary for a trip.

        Args:
            trip_id: UUID of the trip
            destination_name: Selected destination name
            user_id: UUID of the user requesting itinerary

        Returns:
            dict: Itinerary result or error
        """
        try:
            logger.info(f"Generating itinerary for trip {trip_id}, destination: {destination_name}")

            # Load trip context and preferences
            trip_context = load_trip_context(trip_id)
            if "error" in trip_context:
                return {"success": False, "error": trip_context["error"]}

            raw_preferences = load_member_preferences(trip_id)
            if not raw_preferences:
                return {
                    "success": False,
                    "error": "No preferences found. Members must submit preferences first."
                }

            # Check for errors in preferences
            if len(raw_preferences) == 1 and "error" in raw_preferences[0]:
                return {"success": False, "error": raw_preferences[0]["error"]}

            # Aggregate preferences
            aggregated_profile = aggregate_preferences(raw_preferences)

            # Load destination research (from recommendations if available)
            recommendations = load_existing_recommendations(trip_id)
            destination_research = {}
            if recommendations and not isinstance(recommendations, dict) or "error" not in recommendations:
                # Extract research from recommendations for the selected destination
                destinations = recommendations.get("destinations", [])
                for dest in destinations:
                    if dest.get("name") == destination_name:
                        destination_research = {
                            "name": dest.get("name"),
                            "region": dest.get("region"),
                            "reasoning": dest.get("reasoning"),
                            "sources": dest.get("sources", [])
                        }
                        break

            # Initialize session state
            session_state = initialize_session_state(
                trip_context=trip_context,
                raw_preferences=raw_preferences,
                aggregated_group_profile=aggregated_profile,
                selected_destination=destination_name,
                destination_research=destination_research
            )

            # Create and run itinerary workflow
            store_progress(trip_id, "Starting itinerary generation", "initialization")
            workflow_agent = create_itinerary_workflow()

            # Run the workflow
            workflow_result = await workflow_agent.run(
                user_input=f"Generate itinerary for {destination_name}",
                session_state=session_state
            )

            # Extract itinerary from session state
            itinerary_final = session_state.get(SessionStateKeys.ITINERARY_FINAL)

            if not itinerary_final:
                return {
                    "success": False,
                    "error": "Itinerary generation failed to produce output"
                }

            # Store itinerary in database
            itinerary_payload = {
                "destination_name": destination_name,
                "days": itinerary_final.get("days", []),
                "total_cost": itinerary_final.get("total_cost", 0),
                "generated_by": user_id,
                "assumptions": itinerary_final.get("assumptions", []),
                "sources": itinerary_final.get("sources", [])
            }

            store_result = store_itinerary(trip_id, itinerary_payload)

            if not store_result.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to save itinerary: {store_result.get('error')}"
                }

            store_progress(trip_id, "Itinerary generated successfully", "complete")

            return {
                "success": True,
                "itinerary": itinerary_final,
                "itinerary_id": store_result.get("itinerary_id"),
                "generated_at": store_result.get("generated_at")
            }

        except Exception as e:
            logger.error(f"Error generating itinerary: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Itinerary generation failed: {str(e)}"
            }

    async def regenerate_itinerary(
        self,
        trip_id: str,
        feedback: str,
        user_id: str,
        regeneration_count: int = 0
    ) -> Dict[str, Any]:
        """
        Regenerate itinerary with user feedback.

        Args:
            trip_id: UUID of the trip
            feedback: User feedback and modification requests
            user_id: UUID of the user requesting regeneration
            regeneration_count: Current regeneration iteration (for loop bounds)

        Returns:
            dict: Regenerated itinerary result or error
        """
        try:
            logger.info(f"Regenerating itinerary for trip {trip_id} (iteration {regeneration_count})")

            # Check regeneration limit
            MAX_REGENERATIONS = 5
            if regeneration_count >= MAX_REGENERATIONS:
                return {
                    "success": False,
                    "error": f"Maximum regeneration limit reached ({MAX_REGENERATIONS}). Please modify feedback or start fresh."
                }

            # Load existing itinerary
            existing_itinerary = load_existing_itinerary(trip_id)
            if not existing_itinerary or "error" in existing_itinerary:
                return {
                    "success": False,
                    "error": "No existing itinerary found. Generate an itinerary first."
                }

            # Load trip context and preferences
            trip_context = load_trip_context(trip_id)
            if "error" in trip_context:
                return {"success": False, "error": trip_context["error"]}

            raw_preferences = load_member_preferences(trip_id)
            if not raw_preferences:
                return {"success": False, "error": "No preferences found"}

            aggregated_profile = aggregate_preferences(raw_preferences)

            # Initialize session state with existing itinerary and feedback
            session_state = initialize_session_state(
                trip_context=trip_context,
                raw_preferences=raw_preferences,
                aggregated_group_profile=aggregated_profile,
                selected_destination=existing_itinerary.get("destination_name"),
                feedback=feedback,
                regeneration_count=regeneration_count
            )

            # Add existing itinerary to session state
            session_state[SessionStateKeys.ITINERARY_FINAL] = {
                "destination_name": existing_itinerary.get("destination_name"),
                "days": existing_itinerary.get("days", []),
                "total_cost": existing_itinerary.get("total_cost", 0)
            }

            # Create and run regeneration loop
            store_progress(trip_id, f"Starting itinerary regeneration (iteration {regeneration_count + 1})", "regeneration")
            regeneration_agent = create_regeneration_loop_agent(max_iterations=MAX_REGENERATIONS - regeneration_count)

            # Run regeneration
            regeneration_result = await regeneration_agent.run(
                user_input=f"Regenerate itinerary with feedback: {feedback}",
                session_state=session_state
            )

            # Extract regenerated itinerary
            itinerary_final = session_state.get(SessionStateKeys.ITINERARY_FINAL)

            if not itinerary_final:
                return {
                    "success": False,
                    "error": "Regeneration failed to produce updated itinerary"
                }

            # Update itinerary in database (upsert)
            itinerary_payload = {
                "destination_name": itinerary_final.get("destination_name"),
                "days": itinerary_final.get("days", []),
                "total_cost": itinerary_final.get("total_cost", 0),
                "generated_by": user_id,
                "assumptions": itinerary_final.get("assumptions", []),
                "sources": itinerary_final.get("sources", [])
            }

            # Delete old itinerary and insert new one (simplest approach)
            store_result = store_itinerary(trip_id, itinerary_payload)

            if not store_result.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to save regenerated itinerary: {store_result.get('error')}"
                }

            store_progress(trip_id, "Itinerary regenerated successfully", "complete")

            return {
                "success": True,
                "itinerary": itinerary_final,
                "itinerary_id": store_result.get("itinerary_id"),
                "generated_at": store_result.get("generated_at"),
                "regeneration_count": regeneration_count + 1
            }

        except Exception as e:
            logger.error(f"Error regenerating itinerary: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Itinerary regeneration failed: {str(e)}"
            }


# Singleton instance
_agent_service: Optional[AgentService] = None


def get_agent_service() -> AgentService:
    """Get or create the agent service singleton."""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service
