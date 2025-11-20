import random
from typing import List, Optional, Union
from sqlalchemy import Null
from sqlmodel import Session, select, func, null
from api.database import engine
from api.models.sudoku import Sudoku
from api.models.sudoku_image import SudokuImage
from api.models.sudoku_inference import SudokuInference
from core.enums.sudoku_simplified_candidate_type import SudokuSimplifiedCandidateType

class SudokuRepository:
    @classmethod
    def get_all(
            cls,
            n: Optional[int] = None,
            candidate_type: Optional[SudokuSimplifiedCandidateType] = None,
            grid: Optional[List[List[int]]] = None,
            inference_succeeded: Union[Optional[bool], Null] = None,
            has_images: Optional[bool] = None,
            page: Optional[int] = None,
            size: Optional[int] = None
    ) -> List[Sudoku]:
        with Session(engine) as session:
            stmt = select(Sudoku).outerjoin(SudokuInference).outerjoin(SudokuImage).distinct()
            if n is not None:
                stmt = stmt.where(Sudoku.n == n)
            if candidate_type is not None:
                stmt = stmt.where(Sudoku.candidate_type == candidate_type)
            if grid is not None:
                stmt = stmt.where(Sudoku.grid == grid)
            if inference_succeeded is not None:
                stmt = stmt.where(SudokuInference.succeeded == inference_succeeded if not isinstance(inference_succeeded, Null) else Sudoku.inference == null())
            if has_images is not None:
                stmt = stmt.where(SudokuImage.id != null() if has_images else SudokuImage.id == null())
            if page is not None and size is not None:
                stmt = stmt.offset(page * size).limit(size)
            return list(session.exec(stmt).unique().all())

    @classmethod
    def get_by_id(cls, sudoku_id: int) -> Optional[Sudoku]:
        with Session(engine) as session:
            stmt = select(Sudoku).where(Sudoku.id == sudoku_id)
            return session.exec(stmt).first()

    @classmethod
    def get_random(
            cls,
            n: Optional[int] = None,
            candidate_type: Optional[SudokuSimplifiedCandidateType] = None,
            grid: Optional[List[List[int]]] = None,
            inference_succeeded: Union[Optional[bool], Null] = None,
            has_images: Optional[bool] = None
    ) -> Optional[Sudoku]:
        entries: List[Sudoku] = cls.get_all(
            n=n,
            candidate_type=candidate_type,
            grid=grid,
            inference_succeeded=inference_succeeded,
            has_images=has_images
        )

        if not entries:
            return None
        return random.choice(entries)

    @classmethod
    def create(cls, sudoku: Sudoku) -> Optional[Sudoku]:
        with Session(engine) as session:
            stmt = select(Sudoku).where(
                Sudoku.n == sudoku.n,
                Sudoku.candidate_type == sudoku.candidate_type,
                Sudoku.grid == sudoku.grid
            )

            existing = session.scalar(stmt)
            if existing:
                return None

            session.add(sudoku)
            session.commit()
            session.refresh(sudoku)
            return sudoku

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
    def count(
            cls,
            n: Optional[int] = None,
            candidate_type: Optional[SudokuSimplifiedCandidateType] = None,
            grid: Optional[List[List[int]]] = None,
            inference_succeeded: Union[Optional[bool], Null] = None,
            has_images: Optional[bool] = None
    ) -> int:
        with Session(engine) as session:
            stmt = select(func.count(Sudoku.id)).select_from(Sudoku).outerjoin(SudokuInference).outerjoin(SudokuImage).distinct()
            if n is not None:
                stmt = stmt.where(Sudoku.n == n)
            if candidate_type is not None:
                stmt = stmt.where(Sudoku.candidate_type == candidate_type)
            if grid is not None:
                stmt = stmt.where(Sudoku.grid == grid)
            if inference_succeeded is not None:
                stmt = stmt.where(SudokuInference.succeeded == inference_succeeded if not isinstance(inference_succeeded, Null) else Sudoku.inference == null())
            if has_images is not None:
                stmt = stmt.where(SudokuImage.id != null() if has_images else SudokuImage.id == null())
            return session.scalar(stmt)
