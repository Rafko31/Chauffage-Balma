import pytest
from sqlalchemy.orm import Session
from src.pulse_ia.models.base import Organization, Participant, Campaign, AnonymousAnswer
from src.pulse_ia.services.analytics import AnalyticsService
from src.pulse_ia.tests.test_security import db_session, engine
from datetime import datetime

def test_anonymity_threshold_respected(db_session: Session):
    org = Organization(name="Threshold Org", settings={"anonymity_threshold": 3})
    db_session.add(org)
    db_session.commit()

    campaign = Campaign(org_id=org.id, title="Threshold Test", start_date=datetime.utcnow(), survey_version="v1")
    db_session.add(campaign)
    db_session.commit()

    # Add 2 answers (below threshold of 3)
    for i in range(2):
        ans = AnonymousAnswer(
            campaign_id=campaign.id,
            org_id=org.id,
            population="Dept A",
            answers={"q": "v"},
            computed_scores={"m": 0.5}
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
        answers={"q": "v"},
        computed_scores={"m": 0.5}
    )
    db_session.add(ans)
    db_session.commit()

    results = AnalyticsService.get_aggregated_results(db_session, org.id, campaign.id, filters={"population": "Dept A"})
    assert results["status"] == "success"
    assert "maturity_avg" in results["data"]
