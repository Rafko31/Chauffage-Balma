import os
import hashlib
import sys
import traceback
from datetime import datetime, timedelta, UTC
from sqlalchemy.orm import Session
from src.pulse_ia.models.base import (
    Organization, User, UserRole, Campaign, Participant,
    UseCase, UsageStatus, AssessmentTemplate, AssessmentVersion,
    ReportStatus, Report, ParticipationStatus
)
from src.pulse_ia.services.participant import ParticipantService
from src.pulse_ia.services.survey import SurveyService
from src.pulse_ia.services.use_case import UseCaseService
from src.pulse_ia.services.report import ReportService
from src.pulse_ia.services.pdf import run_export_sync
from src.pulse_ia.core.db import SessionLocal
from src.pulse_ia.core.config import settings
from src.pulse_ia.core.security import get_password_hash

def seed_demo_data(skip_pdf: bool = False):
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
                adoption_rules={"states": {"Exposition": {"confidence": 0}}}, # Simple rule for demo
                recommendation_library={},
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
        salt = settings.get_secret_key
        for p in participants:
            participant_hash = hashlib.sha256(f"{campaign.id}:{p.id}:{campaign.hash_salt}:{salt}".encode()).hexdigest()
            existing = db.query(ParticipationStatus).filter_by(campaign_id=campaign.id, participant_hash=participant_hash).first()

            if not existing:
                is_anon = p.external_id in ["EMP001", "EMP003", "EMP005"]
                SurveyService.submit_answer(
                    db,
                    org.id,
                    campaign.id,
                    p.id,
                    answers={"confidence": 0.7, "usage_frequency": 0.4},
                    is_anonymous=is_anon,
                    consent_given=True
                )

        # 5. Use Cases
        uc1 = db.query(UseCase).filter_by(org_id=org.id, title="Planification de la maintenance par IA").first()
        if not uc1:
            UseCaseService.create_use_case(
                db, org.id, "Planification de la maintenance par IA",
                "Utiliser l'IA pour prédire les pannes", UsageStatus.EN_EXPERIMENTATION, "Production"
            )

        uc2 = db.query(UseCase).filter_by(org_id=org.id, title="Analyse prédictive des ventes").first()
        if not uc2:
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

        if not skip_pdf:
            artifacts_dir = settings.ARTIFACTS_DIR
            os.makedirs(artifacts_dir, exist_ok=True)
            pdf_path_dir = os.path.abspath(os.path.join(artifacts_dir, "manufacture_innovante_direction_q1.pdf"))
            pdf_path_ca = os.path.abspath(os.path.join(artifacts_dir, "manufacture_innovante_ca_q1.pdf"))

            report_data = {
                "id": report.id,
                "campaign_title": campaign.title,
                "content": report.content,
                "methodology_snapshot": report.methodology_snapshot,
                "report_version": report.report_version
            }

            # PDF generation is mandatory in demo mode (skip_pdf=False)
            run_export_sync(report_data, pdf_path_dir, template_name="direction_report")
            run_export_sync(report_data, pdf_path_ca, template_name="ca_report")

            # Validation
            for p in [pdf_path_dir, pdf_path_ca]:
                if not os.path.exists(p):
                    raise RuntimeError(f"Failed to generate PDF at {p}")
                with open(p, "rb") as f:
                    if f.read(4) != b"%PDF":
                        raise RuntimeError(f"Generated file {p} is not a valid PDF")

            print(f"Rapport Direction généré : {pdf_path_dir}")
            print(f"Rapport CA généré : {pdf_path_ca}")

        print("Demo data seeded successfully.")

    finally:
        db.close()

if __name__ == "__main__":
    try:
        seed_demo_data()
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
