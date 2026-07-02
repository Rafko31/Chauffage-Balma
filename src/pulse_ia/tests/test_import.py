import pytest
from sqlalchemy.orm import Session
from src.pulse_ia.models.base import Organization, Participant
from src.pulse_ia.services.participant import ParticipantService
from src.pulse_ia.tests.test_security import db_session, engine

def test_import_participants_idempotent(db_session: Session):
    org = Organization(name="Test Org")
    db_session.add(org)
    db_session.commit()

    csv_content = """id,email,dept
EXT001,user1@test.com,IT
EXT002,user2@test.com,HR
"""
    mapping = {
        "external_id": "id",
        "email": "email",
        "direction": "dept"
    }

    # First import
    result = ParticipantService.import_from_csv(db_session, org.id, csv_content, mapping)
    assert result.created == 2
    assert result.total == 2

    # Second import (idempotent)
    result = ParticipantService.import_from_csv(db_session, org.id, csv_content, mapping)
    assert result.created == 0
    assert result.updated == 2

    # Verify data
    stmt = db_session.query(Participant).filter(Participant.external_id == "EXT001")
    p = stmt.first()
    assert p.email == "user1@test.com"
    assert p.direction == "IT"
