from fastapi import FastAPI
from .routers import reccomendations
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
app.include_router(reccomendations.router, prefix="/api/v1", tags=["reccomendations"])

@app.get("/")
async def read_root():
  return {"Hello": "World"}

@app.get("/heath")
def health_check():
  return {"status": "ok"}

