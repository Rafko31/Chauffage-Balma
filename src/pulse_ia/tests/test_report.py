import pytest
from sqlalchemy.orm import Session
from src.pulse_ia.models.base import Organization, Campaign, AnonymousAnswer, Report, ReportStatus, User, UserRole, AssessmentTemplate, AssessmentVersion
from src.pulse_ia.services.report import ReportService

from datetime import datetime, UTC

def test_report_workflow(db_session: Session):
    org = Organization(name="Report Org")
    db_session.add(org)
    db_session.commit()

    user = User(email="admin@reportorg.com", org_id=org.id, role=UserRole.ORGADMIN, hashed_password="pw")
    db_session.add(user)

    template = AssessmentTemplate(title="Report Template")
    db_session.add(template)
    db_session.commit()

    version = AssessmentVersion(
        template_id=template.id, version="v1",
        structure={}, scoring_rules={"maturity": {}, "sentiment": {}, "activation": {}},
        adoption_rules={}, recommendation_library={}
    )
    db_session.add(version)
    db_session.commit()

    campaign = Campaign(org_id=org.id, assessment_version_id=version.id, title="Report Campaign", start_date=datetime.now(UTC), hash_salt="salt")
    db_session.add(campaign)
    db_session.commit()

    # Add enough answers for the threshold
    for i in range(10):
        ans = AnonymousAnswer(
            campaign_id=campaign.id,
            org_id=org.id,
            computed_scores={"maturity": 0.3, "sentiment": 0.5, "activation": 0.2},
                answers={"q1": 1},
                adoption_state="Exploration"
        )
        db_session.add(ans)
    db_session.commit()

    # Create Draft
    report = ReportService.create_draft(db_session, org.id, campaign.id)
    assert report.status == ReportStatus.BROUILLON
    assert len(report.content["recommendations"]) > 0

    # Transitions
    ReportService.transition_to_review(db_session, report.id, org.id)
    assert report.status == ReportStatus.EN_REVISION

    ReportService.approve_report(db_session, report.id, org.id)
    assert report.status == ReportStatus.APPROUVE

    # Publish
    published = ReportService.publish_report(db_session, report.id, org.id, user.id)
    assert published.status == ReportStatus.PUBLIE
    assert published.approved_by_id == user.id
    assert published.published_at is not None
