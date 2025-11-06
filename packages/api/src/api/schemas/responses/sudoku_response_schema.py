from typing import List
from pydantic import BaseModel
from api.enums.sudoku_candidate_type import SudokuCandidateType
from api.schemas.responses.sudoku_image_response_schema import SudokuImageResponseSchema


class SudokuResponseSchema(BaseModel):
    id: int
    n: int
    candidate_type: SudokuCandidateType
    grid: List[List[int]]
    images: List[SudokuImageResponseSchema]
