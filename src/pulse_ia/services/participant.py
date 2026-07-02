import csv
import io
from typing import Dict
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.pulse_ia.models.base import Participant
from src.pulse_ia.schemas.participant import ParticipantMapping, ImportResult

class ParticipantService:
    @staticmethod
    def import_from_csv(db: Session, org_id: int, csv_content: str, mapping: Dict[str, str]) -> ImportResult:
        # org_id must be provided by the security context, never by user input
        f = io.StringIO(csv_content)
        reader = csv.DictReader(f)

        result = ImportResult(total=0, created=0, updated=0, errors=[])

        for row in reader:
            result.total += 1
            try:
                external_id = row.get(mapping.get('external_id'))
                if not external_id:
                    result.errors.append(f"Row {result.total}: Missing external_id")
                    continue

                # Check for existing participant
                stmt = select(Participant).where(
                    Participant.org_id == org_id,
                    Participant.external_id == external_id
                )
                participant = db.execute(stmt).scalar_one_or_none()

                participant_data = {
                    "org_id": org_id,
                    "external_id": external_id,
                    "email": row.get(mapping.get('email')) if mapping.get('email') else None,
                    "population": row.get(mapping.get('population')) if mapping.get('population') else None,
                    "direction": row.get(mapping.get('direction')) if mapping.get('direction') else None,
                    "service": row.get(mapping.get('service')) if mapping.get('service') else None,
                    "equipe": row.get(mapping.get('equipe')) if mapping.get('equipe') else None,
                    "localisation": row.get(mapping.get('localisation')) if mapping.get('localisation') else None,
                }

                if participant:
                    for key, value in participant_data.items():
                        setattr(participant, key, value)
                    result.updated += 1
                else:
                    participant = Participant(**participant_data)
                    db.add(participant)
                    result.created += 1

            except Exception as e:
                result.errors.append(f"Row {result.total}: {str(e)}")

        db.commit()
        return result
