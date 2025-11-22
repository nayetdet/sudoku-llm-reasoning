from pydantic import Field
from api.schemas.queries.base_query_schema import BaseQuerySchema

class SudokuImageQuerySchema(BaseQuerySchema):
    sudoku_id: int = Field(..., exclude=True)
