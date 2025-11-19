from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from api.enums.sudoku_candidate_type import SudokuCandidateType
from api.schemas.responses.sudoku_image_response_schema import SudokuImageResponseSchema


class SudokuResponseSchema(BaseModel):
    id: int
    n: int
    candidate_type: SudokuCandidateType
    grid: List[List[int]]
    images: Optional[List[SudokuImageResponseSchema]] = None
    llm_is_correct: Optional[bool] = None
    llm_checked_at: Optional[datetime] = None
