from typing import Optional
from sqlmodel import Session, select
from api.database import engine
from api.models.sudoku_inference import SudokuInference

class SudokuInferenceRepository:
    @classmethod
    def create(cls, sudoku_inference: SudokuInference) -> Optional[SudokuInference]:
        with Session(engine) as session:
            stmt = select(SudokuInference).where(SudokuInference.sudoku_id == sudoku_inference.id)
            existing = session.exec(stmt).first()
            if existing:
                return None

            session.add(sudoku_inference)
            session.commit()
            session.refresh(sudoku_inference)
            return sudoku_inference
