# test_runner.py
import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from tripsync.orchestration import create_recommendation_workflow

async def test_runner():
    print("Initializing workflow agent...")
    agent = create_recommendation_workflow()
    print("Initializing session service...")
    session_service = InMemorySessionService()
    
    print("Instantiating Runner...")
    runner = Runner(
        agent=agent,
        app_name="tripsync-test",
        session_service=session_service,
    )
    
    print("✓ Runner instantiated successfully")
    
    # Test run_async signature (will fail without valid state/context, but tests import and method existence)
    print("Testing run_async method existence...")
    if hasattr(runner, 'run_async'):
        print("✓ run_async method exists")
    else:
        print("✗ run_async method NOT found")

if __name__ == "__main__":
    asyncio.run(test_runner())
