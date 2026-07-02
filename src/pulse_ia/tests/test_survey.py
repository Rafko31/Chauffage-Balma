import pytest
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.pulse_ia.models.base import Organization, Participant, Campaign, AnonymousAnswer, IdentifiedAnswer, ParticipationStatus, FollowUpRequest, AssessmentTemplate, AssessmentVersion
from src.pulse_ia.services.survey import SurveyService
from src.pulse_ia.tests.test_security import db_session, engine
from datetime import datetime, UTC

def test_anonymous_submission_decoupled(db_session: Session):
    org = Organization(name="Survey Org")
    db_session.add(org)
    db_session.commit()

    participant = Participant(org_id=org.id, external_id="P1", population="Eng")
    db_session.add(participant)

    template = AssessmentTemplate(title="Template 1")
    db_session.add(template)
    db_session.commit()

    version = AssessmentVersion(
        template_id=template.id,
        version="v1",
        structure={},
        scoring_rules={"maturity": {"weights": {"q1": 1.0}}, "sentiment": {}, "activation": {}},
        adoption_rules={},
        recommendation_library={}
    )
    db_session.add(version)
    db_session.commit()

    campaign = Campaign(org_id=org.id, assessment_version_id=version.id, title="Test Campaign", start_date=datetime.now(UTC), hash_salt="salt")
    db_session.add(campaign)
    db_session.commit()

    answers = {"q1": 0.8, "adoption_state": "Exploration"}
    follow_up = {"requested": True, "contact_info": "user@test.com", "message": "Call me"}

    # Submit anonymously
    SurveyService.submit_answer(
        db_session,
            org.id,
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
    assert anon_ans.computed_scores["maturity"] == 0.8
    # This is the crucial check: there is NO participant_id in AnonymousAnswer table
    with pytest.raises(AttributeError):
        getattr(anon_ans, "participant_id")

    # Verify Participation Status exists (to track rate) but is DECOUPLED
    # ParticipationStatus.participant_id no longer exists
    status = db_session.query(ParticipationStatus).filter(ParticipationStatus.campaign_id == campaign.id).first()
    assert status is not None
    assert hasattr(status, "participant_hash")
    assert not hasattr(status, "participant_id")

    # Verify Follow-up is isolated
    fu = db_session.query(FollowUpRequest).filter(FollowUpRequest.campaign_id == campaign.id).first()
    assert fu.contact_info == "user@test.com"
    assert fu.is_anonymous_respondent == True
