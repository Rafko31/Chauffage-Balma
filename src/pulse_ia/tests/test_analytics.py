import pytest
from sqlalchemy.orm import Session
from src.pulse_ia.models.base import Organization, Participant, Campaign, AnonymousAnswer, AssessmentTemplate, AssessmentVersion
from src.pulse_ia.services.analytics import AnalyticsService
from src.pulse_ia.tests.test_security import db_session, engine
from datetime import datetime, UTC

def test_anonymity_threshold_respected(db_session: Session):
    org = Organization(name="Threshold Org", settings={"anonymity_threshold": 3})
    db_session.add(org)
    db_session.commit()

    template = AssessmentTemplate(title="T")
    db_session.add(template)
    db_session.commit()
    version = AssessmentVersion(
        template_id=template.id, version="v1",
        structure={}, scoring_rules={},
        adoption_rules={}, recommendation_library={}
    )
    db_session.add(version)
    db_session.commit()

    campaign = Campaign(org_id=org.id, assessment_version_id=version.id, title="Threshold Test", start_date=datetime.now(UTC), hash_salt="salt")
    db_session.add(campaign)
    db_session.commit()

    # Add 2 answers (below threshold of 3)
    for i in range(2):
        ans = AnonymousAnswer(
            campaign_id=campaign.id,
            org_id=org.id,
            population="Dept A",
            answers={"q1": 1},
            computed_scores={"maturity": 0.5, "sentiment": 0.5, "activation": 0.5},
            adoption_state="Exploration"
        )
        db_session.add(ans)
    db_session.commit()

    # Request aggregated results for Dept A
    results = AnalyticsService.get_aggregated_results(db_session, org.id, campaign.id, filters={"population": "Dept A"})

    assert results["status"] == "threshold_not_reached"
    assert "data" in results and not results["data"]

    # Add 1 more answer (total 3, meeting threshold)
    ans = AnonymousAnswer(
        campaign_id=campaign.id,
        org_id=org.id,
        population="Dept A",
        answers={"q1": 1},
        computed_scores={"maturity": 0.5, "sentiment": 0.5, "activation": 0.5},
        adoption_state="Exploration"
    )
    db_session.add(ans)
    db_session.commit()

    results = AnalyticsService.get_aggregated_results(db_session, org.id, campaign.id, filters={"population": "Dept A"})
    assert results["status"] == "success"
    assert "maturity_avg" in results["data"]
