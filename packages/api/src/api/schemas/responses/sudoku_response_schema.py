from typing import List
from pydantic import BaseModel
from api.schemas.responses.sudoku_image_response_schema import SudokuImageResponseSchema
from core.enums.sudoku_simplified_candidate_type import SudokuSimplifiedCandidateType

class SudokuResponseSchema(BaseModel):
    id: int
    n: int
    candidate_type: SudokuSimplifiedCandidateType
    grid: List[List[int]]
    images: List[SudokuImageResponseSchema]
