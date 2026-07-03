from typing import Dict, Any, List
from sqlalchemy.orm import Session
from src.pulse_ia.models.base import Campaign, AssessmentVersion, IdentifiedAnswer, AnonymousAnswer, ParticipationStatus, Consent, Report, UseCase
from src.pulse_ia.core.config import settings
import hashlib
import random
from datetime import datetime, timedelta, UTC

class BaseService:
    @staticmethod
    def validate_org(obj: Any, org_id: int):
        if obj and hasattr(obj, "org_id") and obj.org_id != org_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Access denied to this resource (cross-tenant violation)")

class SurveyService(BaseService):
    @staticmethod
    def calculate_adoption_state(answers: Dict[str, Any], rules: Dict[str, Any]) -> str:
        """Calcul déterministe de l'état d'adoption."""
        # rules format: {"states": {"Exposition": {"q1": 1, "q2": 0}, ...}}
        # Simplified logic for MVP: match answers with rule thresholds
        for state, criteria in rules.get("states", {}).items():
            match = True
            for q_id, threshold in criteria.items():
                if answers.get(q_id, 0) < threshold:
                    match = False
                    break
            if match:
                return state
        return "Exposition"

    @staticmethod
    def submit_answer(
        db: Session,
        org_id: int,
        campaign_id: int,
        participant_id: int,
        answers: Dict[str, Any],
        is_anonymous: bool,
        consent_given: bool,
        follow_up: dict = None
    ):
        campaign = db.get(Campaign, campaign_id)
        if not campaign:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Campaign not found")
        SurveyService.validate_org(campaign, org_id)

        version = db.get(AssessmentVersion, campaign.assessment_version_id)

        # Calculate Adoption State & Scores
        scores = SurveyService.compute_scores(answers, version.scoring_rules)
        adoption_state = SurveyService.calculate_adoption_state(answers, version.adoption_rules)

        # 1. Check Participation
        salt = settings.get_secret_key
        participant_hash = hashlib.sha256(f"{campaign_id}:{participant_id}:{campaign.hash_salt}:{salt}".encode()).hexdigest()
        existing_status = db.query(ParticipationStatus).filter_by(
            campaign_id=campaign_id, participant_hash=participant_hash
        ).first()
        if existing_status:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Participant already responded to this campaign")

        # 2. Record Participation (Pseudo)
        status = ParticipationStatus(campaign_id=campaign_id, participant_hash=participant_hash)
        db.add(status)

        # 3. Store Answer
        if is_anonymous:
            # Fetch metadata from participant BEFORE decoupling
            from src.pulse_ia.models.base import Participant
            participant = db.get(Participant, participant_id)
            SurveyService.validate_org(participant, org_id)

            jitter = timedelta(seconds=random.randint(-43200, 43200))
            ans = AnonymousAnswer(
                org_id=org_id, campaign_id=campaign_id,
                population=participant.population, direction=participant.direction,
                answers=answers, computed_scores=scores, adoption_state=adoption_state,
                created_at=datetime.now(UTC) + jitter
            )
        else:
            ans = IdentifiedAnswer(
                org_id=org_id, campaign_id=campaign_id, participant_id=participant_id,
                answers=answers, computed_scores=scores, adoption_state=adoption_state
            )
        db.add(ans)

        # 4. Follow-up (Isolated)
        if follow_up and follow_up.get("requested"):
            from src.pulse_ia.models.base import FollowUpRequest
            fu = FollowUpRequest(
                campaign_id=campaign_id,
                org_id=org_id,
                contact_info=follow_up.get("contact_info"),
                message=follow_up.get("message"),
                is_anonymous_respondent=is_anonymous
            )
            db.add(fu)

        db.commit()
        return ans

    @staticmethod
    def compute_scores(answers: dict, scoring_rules: dict) -> dict:
        scores = {"maturity": 0.0, "sentiment": 0.0, "activation": 0.0}
        for dim in scores.keys():
            weights = scoring_rules.get(dim, {}).get("weights", {})
            total_w = sum(weights.values())
            if total_w > 0:
                scores[dim] = sum(float(answers.get(q, 0)) * w for q, w in weights.items()) / total_w
        return scores
