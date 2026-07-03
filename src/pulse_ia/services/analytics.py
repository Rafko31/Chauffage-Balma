from typing import List, Dict, Any
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from src.pulse_ia.models.base import AnonymousAnswer, IdentifiedAnswer, Organization, Campaign, ParticipationStatus

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

        # 1. Fetch Identified Answers
        id_query = db.query(IdentifiedAnswer).filter_by(org_id=org_id, campaign_id=campaign_id)
        # 2. Fetch Anonymous Answers
        anon_query = db.query(AnonymousAnswer).filter_by(org_id=org_id, campaign_id=campaign_id)

        if filters:
            for key, value in filters.items():
                if hasattr(IdentifiedAnswer, key): id_query = id_query.filter(getattr(IdentifiedAnswer, key) == value)
                if hasattr(AnonymousAnswer, key): anon_query = anon_query.filter(getattr(AnonymousAnswer, key) == value)

        id_answers = id_query.all()
        anon_answers = anon_query.all()
        total_count = len(id_answers) + len(anon_answers)


        if total_count < threshold:
            return {
                "count": total_count,
                "status": "threshold_not_reached",
                "message": f"Results hidden (n={total_count} < threshold={threshold})",
                "data": {}
            }

        # Diversity Guard: Check if results are dominated by a single segment
        # to prevent re-identification by elimination
        if filters:
             # If we are already filtering, the threshold check above is the primary guard.
             # In a full system, we'd check if the remainder of the population is also above threshold.
             pass

        # 3. Merge and Compute
        all_scores = [a.computed_scores for a in id_answers] + [a.computed_scores for a in anon_answers]
        all_states = [a.adoption_state for a in id_answers] + [a.adoption_state for a in anon_answers]

        avg_scores = {
            "maturity_avg": sum(s["maturity"] for s in all_scores) / total_count if total_count > 0 else 0,
            "sentiment_avg": sum(s["sentiment"] for s in all_scores) / total_count if total_count > 0 else 0,
            "activation_avg": sum(s["activation"] for s in all_scores) / total_count if total_count > 0 else 0,
        }

        distribution = {}
        for state in ["Exposition", "Exploration", "Expérimentation", "Usage utile", "Intégration", "Diffusion"]:
            distribution[state] = all_states.count(state) / total_count if total_count > 0 else 0

        return {
            "count": total_count,
            "status": "success",
            "data": {
                **avg_scores,
                "adoption_distribution": distribution
            }
        }

    @staticmethod
    def get_trends(
        db: Session,
        org_id: int,
        campaign_ids: List[int]
    ) -> Dict[str, Any]:
        """Calculates movements on the adoption curve between campaigns."""
        if len(campaign_ids) < 2:
            return {"status": "insufficient_data"}

        # Get distribution for each campaign
        campaign_results = []
        for cid in campaign_ids:
            res = AnalyticsService.get_aggregated_results(db, org_id, cid)
            if res["status"] == "success":
                campaign_results.append({
                    "campaign_id": cid,
                    "distribution": res["data"]["adoption_distribution"],
                    "averages": {
                        "maturity": res["data"]["maturity_avg"],
                        "sentiment": res["data"]["sentiment_avg"],
                        "activation": res["data"]["activation_avg"]
                    }
                })

        if len(campaign_results) < 2:
            return {"status": "insufficient_successful_results"}

        # Compare the two latest campaigns
        latest = campaign_results[-1]
        previous = campaign_results[-2]

        diffs = {
            "maturity": latest["averages"]["maturity"] - previous["averages"]["maturity"],
            "sentiment": latest["averages"]["sentiment"] - previous["averages"]["sentiment"],
            "activation": latest["averages"]["activation"] - previous["averages"]["activation"]
        }

        return {
            "status": "success",
            "diffs": diffs,
            "trend": "improving" if sum(diffs.values()) > 0 else "stagnating_or_declining"
        }
