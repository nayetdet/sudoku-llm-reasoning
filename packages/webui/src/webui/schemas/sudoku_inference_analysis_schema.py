from pydantic import BaseModel
from core.enums.sudoku_simplified_candidate_type import SudokuSimplifiedCandidateType

class SudokuInferenceAnalyticsSchema(BaseModel):
    n: int
    candidate_type: SudokuSimplifiedCandidateType
    total_planned: int
    total_beyond: int
    total_hallucinations: int
    total_missed: int
    total_unprocessed: int
    total: int
