from google.adk.agents import Agent, SequentialAgent
from ..utilities.workflow import get_instruction

def generate_reccomendations_workflow():
  # Step 1: Prefernece Normalization Agent
  #
  # Converts vauge, unstructed text into structured preferences with confidence scores.
  # These confidence scores help in understanding the reliability of the preferences.
  preference_normalizer_agent = Agent(
    name="preference_normalizer_agent",
    model="gemini-3-flash-preview",
    description="Normalizes preferences for a trip",
    instruction=get_instruction("preference_normalizer_agent_prompt.txt"),
  )

  # Step 2: AggregationAgent
  #
  # Aggregates preferences for a trip
  # Note: This agent is really a wrapper around the function that will aggregate the preferneces.
  agregation_agent = Agent(
    name="agregation_agent",
    model="gemini-2.5-flash",
    description="Aggregates preferences for a trip",
    instruction=get_instruction("agregation_agent_prompt.txt"),
  )

  # Step 2: Initialize the sequential agent
  generate_reccomendations_seq_agent=SequentialAgent(
    name="generate_reccomendations_workflow",
    description="Generates 3 reccomendations for a trip based on a group's preferences.",
    sub_agents=[preference_normalizer_agent]
  )

  return generate_reccomendations_seq_agent

