import random
from typing import List, Optional
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select, func
from api.database import engine
from api.enums.sudoku_candidate_type import SudokuCandidateType
from api.models.sudoku import Sudoku

class SudokuRepository:
    @classmethod
    def get_all(cls, n: Optional[int] = None, candidate_type: Optional[SudokuCandidateType] = None, grid: Optional[List[List[int]]] = None, page: Optional[int] = None, size: Optional[int] = None) -> List[Sudoku]:
        with Session(engine) as session:
            stmt = select(Sudoku).options(selectinload(Sudoku.images))
            if n is not None:
                stmt = stmt.where(Sudoku.n == n)
            if candidate_type is not None:
                stmt = stmt.where(Sudoku.candidate_type == candidate_type)
            if grid is not None:
                stmt = stmt.where(Sudoku.grid == grid)
            if page is not None and size is not None:
                stmt = stmt.offset(page * size).limit(size)
            return list(session.exec(stmt).all())

    @classmethod
    def get_by_id(cls, sudoku_id: int) -> Optional[Sudoku]:
        with Session(engine) as session:
            stmt = select(Sudoku).where(Sudoku.id == sudoku_id).options(selectinload(Sudoku.images))
            return session.exec(stmt).first()

    @classmethod
    def get_random(cls, n: Optional[int] = None, candidate_type: Optional[SudokuCandidateType] = None, grid: Optional[List[List[int]]] = None) -> Optional[Sudoku]:
        entries: List[Sudoku] = cls.get_all(n=n, candidate_type=candidate_type, grid=grid)
        if not entries:
            return None
        return random.choice(entries)

    @classmethod
    def create(cls, sudoku_model: Sudoku) -> Optional[Sudoku]:
        with Session(engine) as session:
            stmt = select(Sudoku).where(
                Sudoku.n == sudoku_model.n,
                Sudoku.candidate_type == sudoku_model.candidate_type,
                Sudoku.grid == sudoku_model.grid
            )

            existing = session.scalar(stmt)
            if existing:
                return None

            session.add(sudoku_model)
            session.commit()
            session.refresh(sudoku_model)
            return sudoku_model

    @classmethod
    def delete_by_id(cls, sudoku_id: int) -> bool:
        with Session(engine) as session:
            sudoku = session.get(Sudoku, sudoku_id)
            if sudoku is None:
                return False

            session.delete(sudoku)
            session.commit()
            return True

    @classmethod
    def count(cls, n: Optional[int] = None, candidate_type: Optional[SudokuCandidateType] = None, grid: Optional[List[List[int]]] = None) -> int:
        with Session(engine) as session:
            stmt = select(func.count()).select_from(Sudoku)
            if n is not None:
                stmt = stmt.where(Sudoku.n == n)
            if candidate_type is not None:
                stmt = stmt.where(Sudoku.candidate_type == candidate_type)
            if grid is not None:
                stmt = stmt.where(Sudoku.grid == grid)
            return session.scalar(stmt)
