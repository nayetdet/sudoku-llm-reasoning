from datetime import datetime
from typing import List, Optional

from sqlmodel import Session, SQLModel, select

from api.database import engine
from api.models.reasoner_accuracy import ReasonerAccuracy


class ReasonerAccuracyRepository:
    _initialized: bool = False

    @classmethod
    def _ensure_table(cls) -> None:
        if cls._initialized:
            return
        SQLModel.metadata.create_all(engine, tables=[ReasonerAccuracy.__table__])
        cls._initialized = True

    @classmethod
    def list_all(cls) -> List[ReasonerAccuracy]:
        cls._ensure_table()
        with Session(engine) as session:
            stmt = select(ReasonerAccuracy).order_by(ReasonerAccuracy.technique.asc())
            return list(session.exec(stmt).all())

    @classmethod
    def upsert_result(cls, technique: str, sample_size: int, successes: int) -> ReasonerAccuracy:
        cls._ensure_table()
        accuracy: float = successes / sample_size if sample_size else 0.0

        with Session(engine) as session:
            stmt = select(ReasonerAccuracy).where(ReasonerAccuracy.technique == technique)
            record: Optional[ReasonerAccuracy] = session.exec(stmt).one_or_none()

            timestamp = datetime.utcnow()
            if record is None:
                record = ReasonerAccuracy(
                    technique=technique,
                    sample_size=sample_size,
                    success_count=successes,
                    accuracy=accuracy,
                    updated_at=timestamp,
                )
                session.add(record)
            else:
                record.sample_size = sample_size
                record.success_count = successes
                record.accuracy = accuracy
                record.updated_at = timestamp

            session.commit()
            session.refresh(record)
            return record
