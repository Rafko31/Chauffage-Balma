import pytest
from sqlalchemy.orm import Session
from src.pulse_ia.models.base import Organization, User, Participant, Campaign, IdentifiedAnswer, AnonymousAnswer, UseCase, Report
from src.pulse_ia.scripts.seed_demo import seed_demo_data
from src.pulse_ia.core.db import SessionLocal

def test_seed_idempotency():
    # This test should run on a clean DB (migrate already done by Makefile)
    db = SessionLocal()

    # 1. First Seed
    seed_demo_data(skip_pdf=True)

    counts = {
        "orgs": db.query(Organization).count(),
        "users": db.query(User).count(),
        "participants": db.query(Participant).count(),
        "campaigns": db.query(Campaign).count(),
        "answers_id": db.query(IdentifiedAnswer).count(),
        "answers_anon": db.query(AnonymousAnswer).count(),
        "use_cases": db.query(UseCase).count(),
        "reports": db.query(Report).count()
    }

    # 2. Second Seed
    seed_demo_data(skip_pdf=True)

    new_counts = {
        "orgs": db.query(Organization).count(),
        "users": db.query(User).count(),
        "participants": db.query(Participant).count(),
        "campaigns": db.query(Campaign).count(),
        "answers_id": db.query(IdentifiedAnswer).count(),
        "answers_anon": db.query(AnonymousAnswer).count(),
        "use_cases": db.query(UseCase).count(),
        "reports": db.query(Report).count()
    }

    db.close()

    assert new_counts == counts
    assert counts["orgs"] >= 1
    assert counts["users"] >= 2
    assert counts["reports"] >= 1
