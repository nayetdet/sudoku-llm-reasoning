from typing import List, Optional
from sqlmodel import Session, func, select
from api.database import engine
from api.models.sudoku_image import SudokuImage

class SudokuImageRepository:
    @classmethod
    def get_all(cls, sudoku_id: Optional[int] = None, page: Optional[int] = None, size: Optional[int] = None) -> List[SudokuImage]:
        with Session(engine) as session:
            stmt = select(SudokuImage).order_by(SudokuImage.id)
            if sudoku_id is not None:
                stmt = stmt.where(SudokuImage.sudoku_id == sudoku_id)
            if page is not None and size is not None:
                stmt = stmt.offset(page * size).limit(size)
            return list(session.exec(stmt).all())

    @classmethod
    def delete_by_id(cls, image_id: int) -> bool:
        with Session(engine) as session:
            image = session.get(SudokuImage, image_id)
            if image is None:
                return False

            session.delete(image)
            session.commit()
            return True

    @classmethod
    def count(cls, sudoku_id: Optional[int] = None) -> int:
        with Session(engine) as session:
            stmt = select(func.count(SudokuImage.id))
            if sudoku_id is not None:
                stmt = stmt.where(SudokuImage.sudoku_id == sudoku_id)
            return session.scalar(stmt)
