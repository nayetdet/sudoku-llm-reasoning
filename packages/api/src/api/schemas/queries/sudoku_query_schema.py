from typing import Optional
from api.enums.sudoku_candidate_type import SudokuCandidateType
from api.schemas.queries.base_query_schema import BaseQuerySchema

class SudokuQuerySchema(BaseQuerySchema):
    n: Optional[int] = None
    candidate_type: Optional[SudokuCandidateType] = None
