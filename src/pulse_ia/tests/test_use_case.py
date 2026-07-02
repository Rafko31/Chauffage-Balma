import pytest
from sqlalchemy.orm import Session
from src.pulse_ia.models.base import Organization, UseCase, UsageStatus
from src.pulse_ia.services.use_case import UseCaseService
from src.pulse_ia.tests.test_security import db_session, engine

def test_use_case_lifecycle(db_session: Session):
    org = Organization(name="Use Case Org")
    db_session.add(org)
    db_session.commit()

    # Create
    uc = UseCaseService.create_use_case(
        db_session,
        org.id,
        "Assistant Rédaction",
        "Aider à la rédaction de rapports",
        UsageStatus.IDEE
    )
    assert uc.status == UsageStatus.IDEE

    # Update status
    updated_uc = UseCaseService.update_status(db_session, uc.id, UsageStatus.EN_EXPERIMENTATION)
    assert updated_uc.status == UsageStatus.EN_EXPERIMENTATION

    # List
    all_uc = UseCaseService.get_by_org(db_session, org.id)
    assert len(all_uc) == 1
    assert all_uc[0].title == "Assistant Rédaction"
