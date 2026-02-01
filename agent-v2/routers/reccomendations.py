from fastapi import APIRouter
from ..services.reccomendations import generate_reccomendations_service

router = APIRouter()

# TODO: Add authentication middleware
# TODO: Add 2 params: trip_id and Depends(get_current_user)

@router.post("/generate-recommendations")
async def get_recommendations():

  # 1. Basic Validation checks

  # 2. Generate Recommendations
  response = await generate_reccomendations_service("test_trip_id", "test_user_id", "test_session_id")

  # 3. Store in Database

  # 4. Return Recommendations
  return response