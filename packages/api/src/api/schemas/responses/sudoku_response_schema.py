from pydantic import BaseModel
from typing import List
from api.enums.sudoku_candidate_type import SudokuCandidateType

class SudokuResponseSchema(BaseModel):
    n: int
    candidate_type: SudokuCandidateType
    grid: List[List[int]]
