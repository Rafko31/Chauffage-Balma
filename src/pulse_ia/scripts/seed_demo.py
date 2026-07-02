import os
from sqlalchemy.orm import Session
from src.pulse_ia.models.base import Organization, User, UserRole, Campaign, Participant, UseCase, UsageStatus, AssessmentTemplate, AssessmentVersion, ReportStatus, Report
from src.pulse_ia.services.participant import ParticipantService
from src.pulse_ia.services.survey import SurveyService
from src.pulse_ia.services.use_case import UseCaseService
from src.pulse_ia.services.report import ReportService
from src.pulse_ia.services.pdf import run_export_sync
from src.pulse_ia.core.db import SessionLocal
from datetime import datetime, timedelta, UTC

def seed_demo_data():
    db = SessionLocal()
    try:
        # 1. Organization
        org = db.query(Organization).filter_by(name="Manufacture Innovante Inc.").first()
        if not org:
            org = Organization(
                name="Manufacture Innovante Inc.",
                settings={"anonymity_threshold": 3}
            )
            db.add(org)
            db.commit()
            db.refresh(org)

        # 2. Users
        from src.pulse_ia.core.security import get_password_hash
        admin = db.query(User).filter_by(email="admin@manufacture.ia").first()
        if not admin:
            admin = User(
                email="admin@manufacture.ia",
                org_id=org.id,
                role=UserRole.ORGADMIN,
                hashed_password=get_password_hash("password")
            )
            db.add(admin)

        direction = db.query(User).filter_by(email="dg@manufacture.ia").first()
        if not direction:
            direction = User(
                email="dg@manufacture.ia",
                org_id=org.id,
                role=UserRole.DIRECTION,
                hashed_password=get_password_hash("password")
            )
            db.add(direction)
        db.commit()

        # 2.5 Assessment Template & Version
        template = db.query(AssessmentTemplate).filter_by(title="Modèle de Maturité IA Pulse").first()
        if not template:
            template = AssessmentTemplate(title="Modèle de Maturité IA Pulse", description="Évaluation standard")
            db.add(template)
            db.commit()
            db.refresh(template)

        scoring_rules = {
            "maturity": {"weights": {"confidence": 0.5, "usage_frequency": 0.5}},
            "sentiment": {"weights": {"confidence": 1.0}},
            "activation": {"weights": {"usage_frequency": 1.0}}
        }

        version = db.query(AssessmentVersion).filter_by(template_id=template.id, version="v1.0").first()
        if not version:
            version = AssessmentVersion(
                template_id=template.id,
                version="v1.0",
                structure={"questions": [{"id": "confidence", "text": "Confiance"}, {"id": "usage_frequency", "text": "Fréquence"}]},
                scoring_rules=scoring_rules,
                adoption_rules={}, # Added to match schema
                recommendation_library={}, # Added to match schema
                is_frozen=True
            )
            db.add(version)
            db.commit()
            db.refresh(version)

        # 3. Campaign
        campaign = db.query(Campaign).filter_by(org_id=org.id, title="Adoption IA - Cycle Q1").first()
        if not campaign:
            campaign = Campaign(
                org_id=org.id,
                assessment_version_id=version.id,
                title="Adoption IA - Cycle Q1",
                start_date=datetime.now(UTC) - timedelta(days=30),
                end_date=datetime.now(UTC) + timedelta(days=5),
                hash_salt="demo_salt"
            )
            db.add(campaign)
            db.commit()
            db.refresh(campaign)

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
            try:
                SurveyService.submit_answer(
                    db,
                    org.id,
                    campaign.id,
                    p.id,
                    answers={"confidence": 0.7, "usage_frequency": 0.4},
                    is_anonymous=is_anon,
                    consent_given=True
                )
            except Exception as e:
                # Silently skip if already responded (idempotency)
                if "already responded" not in str(e):
                    raise e

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

        # 6. Generate Report
        report = db.query(Report).filter_by(org_id=org.id, campaign_id=campaign.id).first()
        if not report:
            report = ReportService.create_draft(db, org.id, campaign.id)
            ReportService.update_decisions(db, report.id, [
                {"action": "Lancer la formation pilote", "owner": "Direction RH", "deadline": "2024-06-01"},
                {"action": "Valider le budget expérimentation", "owner": "Direction Générale", "deadline": "2024-05-15"}
            ])
            ReportService.transition_to_review(db, report.id, org.id)
            ReportService.approve_report(db, report.id, org.id)
            ReportService.publish_report(db, report.id, org.id, admin.id)
            db.refresh(report)

        pdf_path_dir = "manufacture_innovante_direction_q1.pdf"
        pdf_path_ca = "manufacture_innovante_ca_q1.pdf"

        # Prepare data for rendering (convert model to dict with relationships)
        report_data = {
            "id": report.id,
            "campaign_title": campaign.title,
            "content": report.content,
            "methodology": report.methodology_snapshot,
            "report_version": report.report_version
        }

        run_export_sync(report_data, pdf_path_dir, template_name="direction_report")
        run_export_sync(report_data, pdf_path_ca, template_name="ca_report")

        print(f"Demo data seeded and real PDF generated at {pdf_path}")

    finally:
        db.close()

if __name__ == "__main__":
    # Create tables first (normally handled by migrations, but for MVP demo...)
    from src.pulse_ia.models.base import Base
    from src.pulse_ia.core.db import engine
    Base.metadata.create_all(bind=engine)
    seed_demo_data()
