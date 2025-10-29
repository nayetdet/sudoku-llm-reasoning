import random
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from scripts.database import engine
from scripts.enums.sudoku_model_candidate_type import SudokuModelCandidateType
from scripts.models import SudokuModel

class SudokuModelRepository:
    @classmethod
    def get_all(cls, n: Optional[int] = None, candidate_type: Optional[SudokuModelCandidateType] = None, grid: Optional[str] = None) -> List[SudokuModel]:
        with Session(engine) as session:
            stmt = select(SudokuModel)
            if n is not None:
                stmt = stmt.where(SudokuModel.n == n)
            if candidate_type is not None:
                stmt = stmt.where(SudokuModel.candidate_type == candidate_type)
            if grid is not None:
                stmt = stmt.where(SudokuModel.grid == grid)
            return list(session.scalars(stmt).all())

    @classmethod
    def get_random(cls, n: Optional[int] = None, candidate_type: Optional[SudokuModelCandidateType] = None, grid: Optional[str] = None) -> Optional[SudokuModel]:
        entries: List[SudokuModel] = cls.get_all(n=n, candidate_type=candidate_type, grid=grid)
        if not entries:
            return None
        return random.choice(entries)

    @classmethod
    def create(cls, sudoku_model: SudokuModel) -> Optional[SudokuModel]:
        with Session(engine) as session:
            stmt = select(SudokuModel).where(
                SudokuModel.n == sudoku_model.n,
                SudokuModel.candidate_type == sudoku_model.candidate_type,
                SudokuModel.grid == sudoku_model.grid
            )

            existing = session.scalar(stmt)
            if existing:
                return None
            session.add(sudoku_model)
            session.commit()
            session.refresh(sudoku_model)
            return sudoku_model

    @classmethod
    def exists(cls, n: Optional[int] = None, candidate_type: Optional[SudokuModelCandidateType] = None, grid: Optional[str] = None) -> bool:
        with Session(engine) as session:
            stmt = select(func.count()).select_from(SudokuModel)
            if n is not None:
                stmt = stmt.where(SudokuModel.n == n)
            if candidate_type is not None:
                stmt = stmt.where(SudokuModel.candidate_type == candidate_type)
            if grid is not None:
                stmt = stmt.where(SudokuModel.grid == grid)
            count = session.scalar(stmt)
            return count > 0

    @classmethod
    def count(cls) -> int:
        with Session(engine) as session:
            stmt = select(func.count()).select_from(SudokuModel)
            return session.scalar(stmt)
