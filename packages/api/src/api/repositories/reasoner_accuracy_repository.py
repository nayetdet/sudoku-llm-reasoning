from dataclasses import dataclass
from datetime import datetime
from typing import List

from sqlalchemy import case, func
from sqlmodel import Session, select

from api.database import engine
from api.enums.sudoku_candidate_type import SudokuCandidateType
from api.models.sudoku import Sudoku


@dataclass
class ReasonerAccuracyRecord:
    technique: str
    sample_size: int
    success_count: int
    accuracy: float
    updated_at: datetime


class ReasonerAccuracyRepository:
    _TECHNIQUE_LABELS: dict[SudokuCandidateType, str] = {
        SudokuCandidateType.ZEROTH_LAYER_NAKED_SINGLES: "Naked Singles",
        SudokuCandidateType.ZEROTH_LAYER_HIDDEN_SINGLES: "Hidden Singles",
        SudokuCandidateType.FIRST_LAYER_CONSENSUS: "Consensus Principle",
    }

    @classmethod
    def list_all(cls) -> List[ReasonerAccuracyRecord]:
        with Session(engine) as session:
            stmt = (
                select(
                    Sudoku.candidate_type,
                    func.count(Sudoku.id),
                    func.sum(
                        case(
                            (Sudoku.llm_is_correct.is_(True), 1),
                            else_=0,
                        )
                    ),
                    func.max(Sudoku.llm_checked_at),
                )
                .where(Sudoku.llm_is_correct.is_not(None))
                .group_by(Sudoku.candidate_type)
                .order_by(Sudoku.candidate_type.asc())
            )

            rows = session.exec(stmt).all()

        records: List[ReasonerAccuracyRecord] = []
        for candidate_type, sample_size, success_count, updated_at in rows:
            sample_size = int(sample_size or 0)
            success_count = int(success_count or 0)
            accuracy: float = success_count / sample_size if sample_size else 0.0
            label: str = cls._TECHNIQUE_LABELS.get(candidate_type, candidate_type.value)
            timestamp: datetime = updated_at or datetime.utcnow()
            records.append(
                ReasonerAccuracyRecord(
                    technique=label,
                    sample_size=sample_size,
                    success_count=success_count,
                    accuracy=accuracy,
                    updated_at=timestamp,
                )
            )
        return records
