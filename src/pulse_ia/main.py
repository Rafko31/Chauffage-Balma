from fastapi import FastAPI, Depends
from src.pulse_ia.core.config import settings
from src.pulse_ia.core.db import get_db
from src.pulse_ia.api.api_v1.api import api_router

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {"Hello": "Pulse IA"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/ready")
def ready_check(db = Depends(get_db)):
    from sqlalchemy import text
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")
