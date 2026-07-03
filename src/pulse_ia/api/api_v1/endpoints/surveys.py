from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from src.pulse_ia.api import deps
from src.pulse_ia.core.db import get_db
from src.pulse_ia.services.survey import SurveyService

router = APIRouter()

@router.post("/submit")
def submit_survey(
    *,
    db: Session = Depends(get_db),
    ctx: deps.SecurityContext = Depends(deps.get_security_context),
    campaign_id: int,
    participant_id: int,
    answers: Dict[str, Any],
    is_anonymous: bool,
    consent_given: bool
):
    # ctx.org_id is automatically enforced
    return SurveyService.submit_answer(
        db, ctx.org_id, campaign_id, participant_id, answers, is_anonymous, consent_given
    )
