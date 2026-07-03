from fastapi import APIRouter
from src.pulse_ia.api.api_v1.endpoints import login, surveys

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(surveys.router, prefix="/surveys", tags=["surveys"])
