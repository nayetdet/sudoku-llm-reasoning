from typing import Optional
from sqlmodel import Session, select
from api.database import engine
from api.models.sudoku_inference import SudokuInference

class SudokuInferenceRepository:
    @classmethod
    def create(cls, inference: SudokuInference) -> Optional[SudokuInference]:
        with Session(engine) as session:
            stmt = select(SudokuInference).where(SudokuInference.sudoku_id == inference.id)
            existing = session.exec(stmt).first()
            if existing:
                return None

            session.add(inference)
            session.commit()
            session.refresh(inference)
            return inference

    @classmethod
    def delete_by_id(cls, inference_id: int) -> bool:
        with Session(engine) as session:
            inference = session.get(SudokuInference, inference_id)
            if inference is None:
                return False

            session.delete(inference)
            session.commit()
            return True
