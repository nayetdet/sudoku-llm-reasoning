from pydantic import BaseModel
from api.config import Config

class SudokuBulkRequestSchema(BaseModel):
    target_count: int = Config.API.Sudoku.DEFAULT_TARGET_COUNT
    max_attempts: int = Config.API.Sudoku.DEFAULT_MAX_ATTEMPTS
