from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from api.schemas.responses.sudoku_image_response_schema import SudokuImageResponseSchema
from core.enums.sudoku_simplified_candidate_type import SudokuSimplifiedCandidateType

class SudokuResponseSchema(BaseModel):
    id: int
    n: int
    candidate_type: SudokuSimplifiedCandidateType
    grid: List[List[int]]
    inference_succeeded: Optional[bool] = None
    images: Optional[List[SudokuImageResponseSchema]] = None
