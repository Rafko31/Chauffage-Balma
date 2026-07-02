import random
import hashlib
from datetime import datetime, timedelta, UTC
from sqlalchemy.orm import Session
from src.pulse_ia.models.base import AnonymousAnswer, IdentifiedAnswer, ParticipationStatus, FollowUpRequest, Participant, Consent, Campaign, AssessmentVersion
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

        # 1. Register participation (WHO) - decoupled via hash
        # In a real system, the salt would be campaign-specific and stored securely
        salt = settings.SECRET_KEY
        participant_hash = hashlib.sha256(f"{campaign_id}:{participant_id}:{salt}".encode()).hexdigest()

        participation = ParticipationStatus(
            campaign_id=campaign_id,
            participant_hash=participant_hash
        )
        db.add(participation)

        # 1.5 Register Consent
        consent = Consent(
            participant_id=participant_id,
            campaign_id=campaign_id,
            consent_text_version="v1.0", # Hardcoded for MVP
            mode="anonymous" if is_anonymous else "identified"
        )
        db.add(consent)

        # 2. Store answers (WHAT)
        campaign = db.get(Campaign, campaign_id)
        assessment_version = db.get(AssessmentVersion, campaign.assessment_version_id)

        scores = SurveyService.compute_scores(answers, assessment_version.scoring_rules)

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
    def compute_scores(answers: dict, scoring_rules: dict) -> dict:
        """Calcul déterministe des scores basés sur les règles de la version de l'évaluation."""
        scores = {"maturity": 0.0, "sentiment": 0.0, "activation": 0.0}

        for dimension in scores.keys():
            rules = scoring_rules.get(dimension, {})
            dim_score = 0.0
            total_weight = 0.0

            for q_id, weight in rules.get("weights", {}).items():
                val = answers.get(q_id, 0)
                # Map value if needed (e.g. 1-5 scale to 0.0-1.0)
                # For MVP, assume normalized values in answers
                dim_score += float(val) * weight
                total_weight += weight

            if total_weight > 0:
                scores[dimension] = dim_score / total_weight

        return scores
