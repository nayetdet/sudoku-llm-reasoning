from pydantic import BaseModel
from core.enums.sudoku_simplified_candidate_type import SudokuSimplifiedCandidateType

class SudokuInferenceAnalyticsResponseSchema(BaseModel):
    n: int
    candidate_type: SudokuSimplifiedCandidateType
    total_predicted: int
    total_beyond: int
    total_beyond_non_unique: int
    total_hallucinations: int
    total_missed: int
    total_unprocessed: int
    total: int
