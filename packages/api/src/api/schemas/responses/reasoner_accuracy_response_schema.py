from datetime import datetime

from pydantic import BaseModel


class ReasonerAccuracyResponseSchema(BaseModel):
    technique: str
    sample_size: int
    success_count: int
    accuracy: float
    updated_at: datetime
