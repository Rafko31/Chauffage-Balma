import pytest
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.pulse_ia.models.base import Organization, Participant, Campaign, AnonymousAnswer, IdentifiedAnswer, ParticipationStatus, FollowUpRequest
from src.pulse_ia.services.survey import SurveyService
from src.pulse_ia.tests.test_security import db_session, engine
from datetime import datetime

def test_anonymous_submission_decoupled(db_session: Session):
    org = Organization(name="Survey Org")
    db_session.add(org)
    db_session.commit()

    participant = Participant(org_id=org.id, external_id="P1", population="Eng")
    db_session.add(participant)
    campaign = Campaign(org_id=org.id, title="Test Campaign", start_date=datetime.utcnow(), survey_version="v1")
    db_session.add(campaign)
    db_session.commit()

    answers = {"q1": "val1"}
    follow_up = {"requested": True, "contact_info": "user@test.com", "message": "Call me"}

    # Submit anonymously
    SurveyService.submit_answer(
        db_session,
        campaign.id,
        participant.id,
        answers,
        is_anonymous=True,
        consent_given=True,
        follow_up=follow_up
    )

    # Verify Anonymity: No link between AnonymousAnswer and Participant
    anon_ans = db_session.query(AnonymousAnswer).filter(AnonymousAnswer.campaign_id == campaign.id).first()
    assert anon_ans.population == "Eng"
    assert anon_ans.answers == answers
    # This is the crucial check: there is NO participant_id in AnonymousAnswer table
    with pytest.raises(AttributeError):
        getattr(anon_ans, "participant_id")

    # Verify Participation Status exists (to track rate)
    status = db_session.query(ParticipationStatus).filter(ParticipationStatus.participant_id == participant.id).first()
    assert status is not None

    # Verify Follow-up is isolated
    fu = db_session.query(FollowUpRequest).filter(FollowUpRequest.campaign_id == campaign.id).first()
    assert fu.contact_info == "user@test.com"
    assert fu.is_anonymous_respondent == True
