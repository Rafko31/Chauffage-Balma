from typing import Dict, List, Optional
from pydantic import BaseModel, EmailStr

class ParticipantMapping(BaseModel):
    external_id: str
    email: Optional[str] = None
    population: Optional[str] = None
    direction: Optional[str] = None
    service: Optional[str] = None
    equipe: Optional[str] = None
    gestionnaire_id: Optional[str] = None
    segment_client: Optional[str] = None
    localisation: Optional[str] = None

class ImportResult(BaseModel):
    total: int
    created: int
    updated: int
    errors: List[str]
