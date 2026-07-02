import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from src.pulse_ia.models.base import Base, Organization, User, UserRole, Participant
from src.pulse_ia.core.db import get_db
from src.pulse_ia.main import app

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

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
    # In a real service call, we'd use SecurityContext.org_id
    org1_id = org1.id

    # Simulate a service call that enforces org_id
    p = db_session.execute(
        select(Participant).where(Participant.id == p2.id, Participant.org_id == org1_id)
    ).scalar_one_or_none()

    assert p is None

def test_anonymity_logic(db_session):
    # This will be expanded as we implement the service layer
    pass
