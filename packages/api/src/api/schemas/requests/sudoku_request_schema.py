from pydantic import BaseModel
from typing import Literal
from api.config import Config
from core.enums.sudoku_simplified_candidate_type import SudokuSimplifiedCandidateType

class SudokuRequestSchema(BaseModel):
    n: Literal[4, 9]
    candidate_type: SudokuSimplifiedCandidateType
    target_count: int = Config.API.Sudoku.DEFAULT_TARGET_COUNT
    max_attempts: int = Config.API.Sudoku.DEFAULT_MAX_ATTEMPTS
