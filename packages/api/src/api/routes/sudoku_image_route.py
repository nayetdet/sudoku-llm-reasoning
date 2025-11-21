from fastapi import APIRouter, status
from api.repositories.sudoku_image_repository import SudokuImageRepository

router = APIRouter()

@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_by_id(image_id: int):
    SudokuImageRepository.delete_by_id(image_id)
