from typing import List, Optional
from sqlalchemy.orm import Session
from src.pulse_ia.models.base import UseCase, UsageStatus

class UseCaseService:
    @staticmethod
    def create_use_case(
        db: Session,
        org_id: int,
        title: str,
        description: str = None,
        status: UsageStatus = UsageStatus.IDEE,
        population: str = None
    ) -> UseCase:
        use_case = UseCase(
            org_id=org_id,
            title=title,
            description=description,
            status=status,
            population=population
        )
        db.add(use_case)
        db.commit()
        db.refresh(use_case)
        return use_case

    @staticmethod
    def update_status(db: Session, use_case_id: int, new_status: UsageStatus) -> UseCase:
        use_case = db.get(UseCase, use_case_id)
        if use_case:
            use_case.status = new_status
            db.commit()
            db.refresh(use_case)
        return use_case

    @staticmethod
    def get_by_org(db: Session, org_id: int) -> List[UseCase]:
        return db.query(UseCase).filter(UseCase.org_id == org_id).all()
