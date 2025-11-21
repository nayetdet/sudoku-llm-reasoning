from api.exceptions.sudoku_image_exceptions import SudokuImageNotFoundException
from api.repositories.sudoku_image_repository import SudokuImageRepository

class SudokuImageService:
    @classmethod
    def delete_by_id(cls, image_id: int) -> None:
        if not SudokuImageRepository.delete_by_id(image_id):
            raise SudokuImageNotFoundException()
