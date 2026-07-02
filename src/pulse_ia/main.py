from fastapi import FastAPI
from src.pulse_ia.core.config import settings
from src.pulse_ia.api.api_v1.api import api_router

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {"Hello": "Pulse IA"}
