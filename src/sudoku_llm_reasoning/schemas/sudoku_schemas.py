from typing import Tuple
from pydantic import BaseModel

class SudokuLLMStepSchema(BaseModel):
    step: int
    value: int
    position: Tuple[int, int]
    candidates_before: Tuple[int, ...]
    explanation: str

class SudokuLLMSolutionSchema(BaseModel):
    steps: Tuple[SudokuLLMStepSchema, ...]
    final_grid: Tuple[Tuple[int, ...], ...]
    unique_solution: bool
