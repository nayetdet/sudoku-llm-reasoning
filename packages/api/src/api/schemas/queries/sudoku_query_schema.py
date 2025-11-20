from typing import Optional
from api.schemas.queries.base_query_schema import BaseQuerySchema
from core.enums.sudoku_simplified_candidate_type import SudokuSimplifiedCandidateType

class SudokuQuerySchema(BaseQuerySchema):
    n: Optional[int] = None
    candidate_type: Optional[SudokuSimplifiedCandidateType] = None
    inference_succeeded: Optional[bool] = None
