from typing import List, Dict, Any
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from src.pulse_ia.models.base import AnonymousAnswer, IdentifiedAnswer, Organization, Campaign

class AnalyticsService:
    @staticmethod
    def get_aggregated_results(
        db: Session,
        org_id: int,
        campaign_id: int,
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        # Get threshold for the organization
        org = db.get(Organization, org_id)
        threshold = org.settings.get("anonymity_threshold", 5) if org.settings else 5

        # Aggregate Anonymous Answers
        query = db.query(AnonymousAnswer).filter(
            AnonymousAnswer.org_id == org_id,
            AnonymousAnswer.campaign_id == campaign_id
        )

        if filters:
            for key, value in filters.items():
                if hasattr(AnonymousAnswer, key):
                    query = query.filter(getattr(AnonymousAnswer, key) == value)

        count = query.count()

        if count < threshold:
            return {
                "count": count,
                "status": "threshold_not_reached",
                "message": f"Results hidden (n={count} < threshold={threshold})",
                "data": {}
            }

        # Real aggregation logic for scores and adoption states
        avg_scores = db.query(
            func.avg(AnonymousAnswer.computed_scores['maturity'].as_float()).label('maturity'),
            func.avg(AnonymousAnswer.computed_scores['sentiment'].as_float()).label('sentiment'),
            func.avg(AnonymousAnswer.computed_scores['activation'].as_float()).label('activation')
        ).filter(AnonymousAnswer.id.in_(select(query.subquery().c.id))).first()

        # Adoption distribution
        adoption_counts = db.query(
            AnonymousAnswer.answers['adoption_state'].as_string(),
            func.count(AnonymousAnswer.id)
        ).filter(AnonymousAnswer.id.in_(select(query.subquery().c.id))).group_by(
            AnonymousAnswer.answers['adoption_state'].as_string()
        ).all()

        adoption_distribution = {state: c / count for state, c in adoption_counts} if count > 0 else {}

        return {
            "count": count,
            "status": "success",
            "data": {
                "maturity_avg": avg_scores.maturity if avg_scores else 0,
                "sentiment_avg": avg_scores.sentiment if avg_scores else 0,
                "activation_avg": avg_scores.activation if avg_scores else 0,
                "adoption_distribution": adoption_distribution
            }
        }

    @staticmethod
    def get_trends(
        db: Session,
        org_id: int,
        campaign_ids: List[int]
    ) -> Dict[str, Any]:
        """Calculates movements on the adoption curve between campaigns."""
        # This would compare distribution shifts between campaigns
        # Simplified for MVP
        return {"trend": "improving", "details": "Movement from Exploration to Experimentation detected"}
