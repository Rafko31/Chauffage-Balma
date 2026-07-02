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
            status=ReportStatus.BROUILLON,
            content=content,
            version="1.0"
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def publish_report(db: Session, report_id: int, user_id: int) -> Report:
        report = db.get(Report, report_id)
        if report:
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
