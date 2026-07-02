import os
from sqlalchemy.orm import Session
from src.pulse_ia.models.base import Organization, User, UserRole, Campaign, Participant, UseCase, UsageStatus
from src.pulse_ia.services.participant import ParticipantService
from src.pulse_ia.services.survey import SurveyService
from src.pulse_ia.services.use_case import UseCaseService
from src.pulse_ia.core.db import SessionLocal
from datetime import datetime, timedelta

def seed_demo_data():
    db = SessionLocal()
    try:
        # 1. Organization
        org = Organization(
            name="Manufacture Innovante Inc.",
            settings={"anonymity_threshold": 3}
        )
        db.add(org)
        db.commit()

        # 2. Users
        admin = User(
            email="admin@manufacture.ia",
            org_id=org.id,
            role=UserRole.ORGADMIN,
            hashed_password="hashed_password" # In production use pwd_context.hash()
        )
        direction = User(
            email="dg@manufacture.ia",
            org_id=org.id,
            role=UserRole.DIRECTION,
            hashed_password="hashed_password"
        )
        db.add_all([admin, direction])

        # 3. Campaign
        campaign = Campaign(
            org_id=org.id,
            title="Adoption IA - Cycle Q1",
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow() + timedelta(days=5),
            survey_version="v1.0"
        )
        db.add(campaign)
        db.commit()

        # 4. Participants & Answers
        csv_content = """id,email,dept,role
EMP001,alice@manufacture.ia,Production,Opérateur
EMP002,bob@manufacture.ia,R&D,Ingénieur
EMP003,charlie@manufacture.ia,RH,Généraliste
EMP004,david@manufacture.ia,Ventes,Directeur
EMP005,eve@manufacture.ia,Production,Chef d'équipe
"""
        mapping = {"external_id": "id", "email": "email", "direction": "dept", "population": "role"}
        ParticipantService.import_from_csv(db, org.id, csv_content, mapping)

        participants = db.query(Participant).filter(Participant.org_id == org.id).all()

        # Mix of identified and anonymous answers
        for p in participants:
            is_anon = p.external_id in ["EMP001", "EMP003", "EMP005"]
            SurveyService.submit_answer(
                db,
                campaign.id,
                p.id,
                answers={"adoption_state": "Exploration", "confidence": 4},
                is_anonymous=is_anon,
                consent_given=True
            )

        # 5. Use Cases
        UseCaseService.create_use_case(
            db, org.id, "Planification de la maintenance par IA",
            "Utiliser l'IA pour prédire les pannes", UsageStatus.EN_EXPERIMENTATION, "Production"
        )
        UseCaseService.create_use_case(
            db, org.id, "Analyse prédictive des ventes",
            "Prédire les ventes du prochain trimestre", UsageStatus.IDEE, "Ventes"
        )

        db.commit()
        print("Demo data seeded for Manufacture Innovante Inc.")

    finally:
        db.close()

if __name__ == "__main__":
    # Create tables first (normally handled by migrations, but for MVP demo...)
    from src.pulse_ia.models.base import Base
    from src.pulse_ia.core.db import engine
    Base.metadata.create_all(bind=engine)
    seed_demo_data()
