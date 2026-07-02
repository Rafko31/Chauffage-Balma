import random
from datetime import datetime, timedelta, UTC
from sqlalchemy.orm import Session
from src.pulse_ia.models.base import AnonymousAnswer, IdentifiedAnswer, ParticipationStatus, FollowUpRequest, Participant
from src.pulse_ia.core.config import settings

class SurveyService:
    @staticmethod
    def submit_answer(
        db: Session,
        campaign_id: int,
        participant_id: int,
        answers: dict,
        is_anonymous: bool,
        consent_given: bool,
        follow_up: dict = None
    ):
        if not consent_given:
            raise ValueError("Consent is required to submit answers.")

        participant = db.get(Participant, participant_id)
        if not participant:
            raise ValueError("Participant not found")

        # 1. Register participation (WHO) - decouple from WHAT
        participation = ParticipationStatus(
            campaign_id=campaign_id,
            participant_id=participant_id
        )
        db.add(participation)

        # 2. Store answers (WHAT)
        # Compute scores (placeholder for now)
        scores = SurveyService.compute_scores(answers)

        if is_anonymous:
            # Jittering: add/subtract up to 12 hours to prevent temporal correlation
            jitter = timedelta(seconds=random.randint(-43200, 43200))

            # Metadata only, no link to participant_id
            ans = AnonymousAnswer(
                campaign_id=campaign_id,
                org_id=participant.org_id,
                population=participant.population,
                direction=participant.direction,
                service=participant.service,
                equipe=participant.equipe,
                localisation=participant.localisation,
                answers=answers,
                computed_scores=scores,
                created_at=datetime.now(UTC) + jitter
            )
        else:
            ans = IdentifiedAnswer(
                campaign_id=campaign_id,
                participant_id=participant_id,
                answers=answers,
                computed_scores=scores
            )
        db.add(ans)

        # 3. Follow-up (Isolated)
        if follow_up and follow_up.get("requested"):
            fu = FollowUpRequest(
                campaign_id=campaign_id,
                org_id=participant.org_id,
                contact_info=follow_up.get("contact_info"),
                message=follow_up.get("message"),
                is_anonymous_respondent=is_anonymous
            )
            db.add(fu)

        db.commit()
        return ans

    @staticmethod
    def compute_scores(answers: dict) -> dict:
        # Placeholder score computation
        # In real scenario, this would use the survey_version logic
        return {"maturity": 0.5, "sentiment": 0.7, "activation": 0.4}
