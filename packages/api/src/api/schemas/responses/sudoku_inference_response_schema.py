from pydantic import BaseModel

class SudokuInferenceResponseSchema(BaseModel):
    id: int
    succeeded: bool
    explanation: str
