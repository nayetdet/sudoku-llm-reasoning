from typing import List, Optional
from pydantic import BaseModel
from api.schemas.responses.sudoku_inference_response_schema import SudokuInferenceResponseSchema
from core.enums.sudoku_simplified_candidate_type import SudokuSimplifiedCandidateType

class SudokuResponseSchema(BaseModel):
    id: int
    n: int
    candidate_type: SudokuSimplifiedCandidateType
    grid: List[List[int]]
    inference: Optional[SudokuInferenceResponseSchema] = None
