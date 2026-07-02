from fastapi import FastAPI
from src.pulse_ia.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

@app.get("/")
def read_root():
    return {"Hello": "Pulse IA"}
