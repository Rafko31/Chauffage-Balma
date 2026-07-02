import pytest
from sqlalchemy.orm import Session
from src.pulse_ia.models.base import Organization, Campaign, AnonymousAnswer, Report, ReportStatus, User, UserRole
from src.pulse_ia.services.report import ReportService
from src.pulse_ia.tests.test_security import db_session, engine
from datetime import datetime

def test_report_workflow(db_session: Session):
    org = Organization(name="Report Org")
    db_session.add(org)
    db_session.commit()

    user = User(email="admin@reportorg.com", org_id=org.id, role=UserRole.ORGADMIN, hashed_password="pw")
    db_session.add(user)

    campaign = Campaign(org_id=org.id, title="Report Campaign", start_date=datetime.utcnow(), survey_version="v1")
    db_session.add(campaign)
    db_session.commit()

    # Add enough answers for the threshold
    for i in range(10):
        ans = AnonymousAnswer(
            campaign_id=campaign.id,
            org_id=org.id,
            computed_scores={"maturity": 0.3, "sentiment": 0.5, "activation": 0.2},
            answers={"adoption_state": "Exploration"}
        )
        db_session.add(ans)
    db_session.commit()

    # Create Draft
    report = ReportService.create_draft(db_session, org.id, campaign.id)
    assert report.status == ReportStatus.BROUILLON
    assert len(report.content["recommendations"]) > 0

    # Publish
    published = ReportService.publish_report(db_session, report.id, user.id)
    assert published.status == ReportStatus.PUBLIE
    assert published.approved_by_id == user.id
    assert published.published_at is not None
