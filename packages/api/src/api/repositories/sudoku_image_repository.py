from sqlmodel import Session
from api.database import engine
from api.models.sudoku_image import SudokuImage

class SudokuImageRepository:
    @classmethod
    def delete_by_id(cls, image_id: int) -> bool:
        with Session(engine) as session:
            image = session.get(SudokuImage, image_id)
            if image is None:
                return False

            session.delete(image)
            session.commit()
            return True
