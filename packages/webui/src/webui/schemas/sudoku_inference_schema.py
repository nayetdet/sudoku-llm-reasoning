from typing import Optional
from pydantic import BaseModel

class SudokuInferenceSchema(BaseModel):
    id: int
    succeeded: bool
    succeeded_nth_layer: bool
    succeeded_and_unique_nth_layer: bool
    explanation: Optional[str]
