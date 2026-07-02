from sqlalchemy.orm import Session
from src.pulse_ia.models.base import AssessmentVersion, Campaign, Report
from fastapi import HTTPException

class AssessmentService:
    @staticmethod
    def freeze_version(db: Session, version_id: int):
        version = db.get(AssessmentVersion, version_id)
        if version:
            version.is_frozen = True
            db.commit()
        return version

    @staticmethod
    def check_immutability(db: Session, version_id: int):
        """Raises if version is used in active campaigns or published reports."""
        version = db.get(AssessmentVersion, version_id)
        if not version:
            return

        if version.is_frozen:
            raise HTTPException(status_code=400, detail="Assessment version is frozen and cannot be modified")

        # Check for campaigns using this version
        active_campaign = db.query(Campaign).filter(Campaign.assessment_version_id == version_id).first()
        if active_campaign:
            raise HTTPException(status_code=400, detail="Assessment version is used in a campaign and is now immutable")

        # Check for reports using this version
        published_report = db.query(Report).filter(Report.assessment_version_id == version_id).first()
        if published_report:
             raise HTTPException(status_code=400, detail="Assessment version is used in a report and is now immutable")
