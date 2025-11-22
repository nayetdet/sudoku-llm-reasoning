from typing import List, Optional
from pydantic import BaseModel
from core.enums.sudoku_simplified_candidate_type import SudokuSimplifiedCandidateType
from webui.schemas.sudoku_inference_schema import SudokuInferenceSchema

class SudokuSchema(BaseModel):
    id: int
    n: int
    candidate_type: SudokuSimplifiedCandidateType
    grid: List[List[int]]
    inference: Optional[SudokuInferenceSchema] = None
