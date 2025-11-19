from typing import List

from api.repositories.reasoner_accuracy_repository import ReasonerAccuracyRepository
from api.schemas.responses.reasoner_accuracy_response_schema import ReasonerAccuracyResponseSchema


class ReasonerAccuracyService:
    @classmethod
    def list_results(cls) -> List[ReasonerAccuracyResponseSchema]:
        records = ReasonerAccuracyRepository.list_all()
        return [
            ReasonerAccuracyResponseSchema(
                technique=record.technique,
                sample_size=record.sample_size,
                success_count=record.success_count,
                accuracy=record.accuracy,
                updated_at=record.updated_at,
            )
            for record in records
        ]
