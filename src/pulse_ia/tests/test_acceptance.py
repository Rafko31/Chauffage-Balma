import pytest
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.pulse_ia.models.base import Organization, User, UserRole, Participant, Campaign, Report, ReportStatus, AssessmentTemplate, AssessmentVersion
from src.pulse_ia.services.report import ReportService
from src.pulse_ia.services.analytics import AnalyticsService
from src.pulse_ia.tests.test_security import db_session, engine
from datetime import datetime, UTC

def test_full_business_workflow(db_session: Session):
    # 1. Setup Organizations
    org_ia = Organization(name="Manufacture Innovante Inc.", settings={"anonymity_threshold": 2})
    org_competitor = Organization(name="Competitor Ltd")
    db_session.add_all([org_ia, org_competitor])
    db_session.commit()

    # 2. Setup Evaluation Model
    template = AssessmentTemplate(title="AI Adoption Framework")
    db_session.add(template)
    db_session.commit()

    version = AssessmentVersion(
        template_id=template.id,
        version="v1.0",
        structure={},
        scoring_rules={
            "maturity": {"weights": {"q1": 1.0}},
            "sentiment": {"weights": {"q2": 1.0}},
            "activation": {"weights": {"q3": 1.0}}
        }
    )
    db_session.add(version)
    db_session.commit()

    # 3. Setup Campaigns
    campaign = Campaign(org_id=org_ia.id, assessment_version_id=version.id, title="Q1 Survey", start_date=datetime.now(UTC))
    comp_campaign = Campaign(org_id=org_competitor.id, assessment_version_id=version.id, title="Spying Campaign", start_date=datetime.now(UTC))
    db_session.add_all([campaign, comp_campaign])
    db_session.commit()

    # 4. Access Denied Test
    with pytest.raises(ValueError, match="Campaign not found or access denied"):
        ReportService.create_draft(db_session, org_ia.id, comp_campaign.id)

    # 5. Workflow Immutability
    report = ReportService.create_draft(db_session, org_ia.id, campaign.id)
    assert report.status == ReportStatus.BROUILLON

    # Cannot publish draft directly
    user = User(email="boss@manufacture.ia", org_id=org_ia.id, role=UserRole.DIRECTION, hashed_password="pw")
    db_session.add(user)
    db_session.commit()

    with pytest.raises(ValueError, match="Only approved reports can be published"):
        ReportService.publish_report(db_session, report.id, org_ia.id, user.id)

    # Full successful transition
    ReportService.transition_to_review(db_session, report.id, org_ia.id)
    ReportService.approve_report(db_session, report.id, org_ia.id)
    ReportService.publish_report(db_session, report.id, org_ia.id, user.id)

    assert report.status == ReportStatus.PUBLIE

    # Cannot modify published report
    with pytest.raises(ValueError, match="Only Brouillon can be sent to review"):
        # transition_to_review check: if report.status != BROUILLON
        ReportService.transition_to_review(db_session, report.id, org_ia.id)

    # Immutability of content
    original_content = report.content.copy()
    # Try updating decisions (which calls db.get and checks status)
    updated = ReportService.update_decisions(db_session, report.id, [{"action": "Invest in AI"}])
    assert updated.content == original_content # Should NOT change because status is PUBLIE
