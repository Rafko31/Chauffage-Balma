import pytest
from sqlalchemy.orm import Session
from src.pulse_ia.models.base import Organization, User, Participant, Campaign, IdentifiedAnswer, AnonymousAnswer, UseCase, Report
from src.pulse_ia.scripts.seed_demo import seed_demo_data
from src.pulse_ia.core.db import SessionLocal

def test_seed_full_and_idempotent():
    # This test should run on a clean DB (migrate already done by Makefile)
    db = SessionLocal()

    # 1. First Seed (Full with PDF)
    # Note: Inside Docker api container, playwright is available
    seed_demo_data(skip_pdf=False)

    # Check PDF integrity
    artifacts_dir = settings.ARTIFACTS_DIR
    pdf_dir = os.path.join(artifacts_dir, "manufacture_innovante_direction_q1.pdf")
    pdf_ca = os.path.join(artifacts_dir, "manufacture_innovante_ca_q1.pdf")

    for p in [pdf_dir, pdf_ca]:
        assert os.path.exists(p)
        with open(p, "rb") as f:
            assert f.read(4) == b"%PDF"

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
