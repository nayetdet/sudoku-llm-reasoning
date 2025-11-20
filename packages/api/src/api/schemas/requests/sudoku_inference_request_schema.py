from typing import List, Literal
from pydantic import BaseModel
from api.config import Config
from core.enums.sudoku_simplified_candidate_type import SudokuSimplifiedCandidateType

class SudokuInferenceRequestSchema(BaseModel):
    ns: List[Literal[4, 9]] = [4, 9]
    candidate_types: List[SudokuSimplifiedCandidateType] = list(SudokuSimplifiedCandidateType)
    target_count: int = Config.Sudoku.DEFAULT_TARGET_COUNT
