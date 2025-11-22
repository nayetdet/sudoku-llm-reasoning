from copy import deepcopy
from api.schemas.queries.sudoku_image_query_schema import SudokuImageQuerySchema
from api.schemas.responses.sudoku_image_response_schema import SudokuImageResponseSchema
from api.services.sudoku_image_service import SudokuImageService
from fastapi import APIRouter, Depends, status
from api.schemas.queries.base_query_schema import PageSchema
from api.schemas.queries.sudoku_query_schema import SudokuQuerySchema
from api.schemas.requests.sudoku_request_schema import SudokuRequestSchema
from api.schemas.responses.sudoku_response_schema import SudokuResponseSchema
from api.services.sudoku_service import SudokuService

router = APIRouter()

@router.get("/", response_model=PageSchema[SudokuResponseSchema])
def get_all(query: SudokuQuerySchema = Depends()):
    return SudokuService.get_all(query)

@router.get("/{sudoku_id}/images", response_model=PageSchema[SudokuImageResponseSchema])
def get_all_images(sudoku_id: int, query: SudokuImageQuerySchema = Depends()):
    q: SudokuImageQuerySchema = deepcopy(query)
    q.sudoku_id = sudoku_id
    return SudokuImageService.get_all(q)

@router.get("/{sudoku_id}", response_model=SudokuResponseSchema)
def get_by_id(sudoku_id: int):
    return SudokuService.get_by_id(sudoku_id)

@router.post("/", status_code=status.HTTP_204_NO_CONTENT)
def create(request: SudokuRequestSchema):
    SudokuService.create(request)

@router.delete("/{sudoku_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_by_id(sudoku_id: int):
    SudokuService.delete_by_id(sudoku_id)
