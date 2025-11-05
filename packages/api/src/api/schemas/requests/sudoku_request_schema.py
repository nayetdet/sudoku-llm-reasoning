from pydantic import BaseModel
from typing import Literal
from api.enums.sudoku_candidate_type import SudokuCandidateType

class SudokuRequestSchema(BaseModel):
    n: Literal[4, 9]
    candidate_type: SudokuCandidateType
    target_count: int = 150
    max_attempts: int = 1000
