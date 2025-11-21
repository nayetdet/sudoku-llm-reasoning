from fastapi import APIRouter, status
from api.services.sudoku_image_service import SudokuImageService

router = APIRouter()

@router.get("/zip")
def download_zip():
    return SudokuImageService.download_zip()

@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_by_id(image_id: int):
    SudokuImageService.delete_by_id(image_id)
