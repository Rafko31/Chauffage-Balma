import pytest
from sqlalchemy import select
from src.pulse_ia.models.base import Organization, User, UserRole, Participant

def test_tenant_isolation(db_session):
    # Create two organizations
    org1 = Organization(name="Org 1")
    org2 = Organization(name="Org 2")
    db_session.add(org1)
    db_session.add(org2)
    db_session.commit()

    # Add a user to Org 1
    user1 = User(email="user1@org1.com", org_id=org1.id, role=UserRole.ORGADMIN, hashed_password="pw")
    db_session.add(user1)
    db_session.commit()

    assert user1.org_id == org1.id
    assert user1.organization.name == "Org 1"

def test_inter_tenant_access_denied(db_session):
    org1 = Organization(name="Org 1")
    org2 = Organization(name="Org 2")
    db_session.add_all([org1, org2])
    db_session.commit()

    # Participant in Org 2
    p2 = Participant(org_id=org2.id, external_id="P2")
    db_session.add(p2)
    db_session.commit()

    # User in Org 1 tries to access p2
    org1_id = org1.id

    # Simulate a service call that enforces org_id
    p = db_session.execute(
        select(Participant).where(Participant.id == p2.id, Participant.org_id == org1_id)
    ).scalar_one_or_none()

    assert p is None

def test_db_type(db_session):
    """Assertion demandée : vérifier le dialecte Postgres."""
    assert db_session.bind.dialect.name == "postgresql"
