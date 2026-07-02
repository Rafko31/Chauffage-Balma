import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from src.pulse_ia.models.base import Organization, User, UserRole, Participant, Campaign, AssessmentTemplate, AssessmentVersion
from src.pulse_ia.core import security
from src.pulse_ia.main import app

from datetime import datetime, UTC

def test_api_cross_tenant_prevention(client, db_session: Session):
    # 1. Setup two organizations
    org1 = Organization(name="Org 1")
    org2 = Organization(name="Org 2")
    db_session.add_all([org1, org2])
    db_session.commit()

    # 2. Setup user for Org 1
    user1 = User(
        email="user1@org1.com",
        org_id=org1.id,
        role=UserRole.ORGADMIN,
        hashed_password=security.get_password_hash("password")
    )
    db_session.add(user1)
    db_session.commit()
    db_session.refresh(user1)

    # 3. Setup campaign for Org 2
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
    campaign2 = Campaign(org_id=org2.id, assessment_version_id=version.id, title="C2", start_date=datetime.now(UTC), hash_salt="s")
    db_session.add(campaign2)
    db_session.commit()

    # 4. Authenticate as User 1
    token = security.create_access_token({"sub": str(user1.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # Add dummy participant to Org 1 for id 1
    p1 = Participant(org_id=org1.id, external_id="P1")
    db_session.add(p1)
    db_session.commit()

    # 5. Try to submit survey for Org 2's campaign
    response = client.post(
        f"/api/v1/surveys/submit?campaign_id={campaign2.id}&participant_id={p1.id}&is_anonymous=true&consent_given=true",
        json={"q1": 1},
        headers=headers
    )

    # Must be 403 Forbidden (or 404 if we want to hide existence, but service raises 403)
    assert response.status_code == 403
    assert "cross-tenant violation" in response.json()["detail"]
