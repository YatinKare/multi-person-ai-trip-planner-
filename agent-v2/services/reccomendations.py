from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from ..workflows.reccomendations import generate_reccomendations_workflow
from google.genai import types

APP_NAME = "tripsync"

async def generate_reccomendations_service(trip_id: str, user_id: str, session_id: str):

  # Initialize session service
  session_service = InMemorySessionService()
  await session_service.create_session(
    app_name=APP_NAME,
    user_id=user_id,
    session_id=session_id,
  )

  runner = Runner(
    agent=generate_reccomendations_workflow(),
    app_name=APP_NAME,
    session_service=session_service,
  )

  content = types.Content(role="user", parts=[types.Part(text="")])
  async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
    # DEBUG:
    print(f"[EVENT] Author: {event.author} Type: {type(event).__name__} Final: {event.is_final_response()} Content: {event.content}")

    if event.is_final_response():
      if event.content and event.content.parts:
        await session_service.delete_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
        return event.content.parts[0].text

  await session_service.delete_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
  return "No response from agent"
