from datetime import datetime, UTC
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from src.pulse_ia.models.base import Report, ReportStatus, Campaign, Organization
from src.pulse_ia.services.analytics import AnalyticsService

class RecommendationService:
    @staticmethod
    def get_recommendations(scores: Dict[str, float]) -> List[Dict[str, str]]:
        recs = []
        if scores.get("maturity_avg", 1.0) < 0.4:
            recs.append({
                "title": "Atelier de sensibilisation",
                "content": "Organiser un atelier pour démystifier l'IA auprès des équipes.",
                "target": "Tous"
            })
        if scores.get("activation_avg", 1.0) < 0.5:
            recs.append({
                "title": "Canevas de cas d'usage",
                "content": "Diffuser le canevas structuré pour aider à identifier des opportunités.",
                "target": "Gestionnaires"
            })
        return recs

class ReportService:
    @staticmethod
    def create_draft(db: Session, org_id: int, campaign_id: int) -> Report:
        campaign = db.get(Campaign, campaign_id)
        if not campaign or campaign.org_id != org_id:
            raise ValueError("Campaign not found or access denied")

        # 1. Fetch data
        results = AnalyticsService.get_aggregated_results(db, org_id, campaign_id)

        # 2. Get recommendations
        recommendations = RecommendationService.get_recommendations(results["data"])

        # 3. Create content snapshot
        content = {
            "results": results["data"],
            "recommendations": recommendations,
            "executive_summary": "Analyse de la maturité et de l'adoption de l'IA.",
            "decisions": [] # To be filled by humans
        }

        report = Report(
            org_id=org_id,
            campaign_id=campaign_id,
            assessment_version_id=campaign.assessment_version_id,
            status=ReportStatus.BROUILLON,
            content=content,
            version="1.0"
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def transition_to_review(db: Session, report_id: int, org_id: int) -> Report:
        report = db.get(Report, report_id)
        if not report or report.org_id != org_id:
            raise ValueError("Report not found or access denied")
        if report.status != ReportStatus.BROUILLON:
            raise ValueError("Only Brouillon can be sent to review")
        report.status = ReportStatus.EN_REVISION
        db.commit()
        return report

    @staticmethod
    def approve_report(db: Session, report_id: int, org_id: int) -> Report:
        report = db.get(Report, report_id)
        if not report or report.org_id != org_id:
            raise ValueError("Report not found or access denied")
        if report.status != ReportStatus.EN_REVISION:
            raise ValueError("Only reports En révision can be approved")
        report.status = ReportStatus.APPROUVE
        db.commit()
        return report

    @staticmethod
    def publish_report(db: Session, report_id: int, org_id: int, user_id: int) -> Report:
        report = db.get(Report, report_id)
        if not report or report.org_id != org_id:
            raise ValueError("Report not found or access denied")
        if report.status != ReportStatus.APPROUVE:
            raise ValueError("Only approved reports can be published")

        # Snapshot is already partially done in create_draft/update_decisions
        # For full immuability, we ensure status is PUBLIE and timestamped
        report.status = ReportStatus.PUBLIE
        report.approved_by_id = user_id
        report.published_at = datetime.now(UTC)
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def update_decisions(db: Session, report_id: int, decisions: List[Dict[str, Any]]) -> Report:
        """Ajoute les décisions de la direction au plan d'action du rapport."""
        report = db.get(Report, report_id)
        if report and report.status != ReportStatus.PUBLIE:
            content = dict(report.content)
            content["decisions"] = decisions
            report.content = content
            db.commit()
            db.refresh(report)
        return report
