from pydantic import BaseModel

class SudokuBulkRequestSchema(BaseModel):
    target_count: int = 150
    max_attempts: int = 1000
