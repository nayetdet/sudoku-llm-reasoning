from typing import Tuple
from pydantic import BaseModel
from packages.core.src.core.enums.sudoku_simplified_candidate_type import SudokuSimplifiedCandidateType

class SudokuLLMCandidateSchema(BaseModel):
    value: int
    position: Tuple[int, int]
    candidate_type: SudokuSimplifiedCandidateType
    explanation: str
