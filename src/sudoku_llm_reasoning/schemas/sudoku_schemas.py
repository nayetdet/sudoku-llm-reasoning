from typing import List
from pydantic import BaseModel

class SudokuLLMStepSchema(BaseModel):
    step: int
    cell: List[int]
    value: int
    candidates_before: List[int]
    explanation: str

class SudokuLLMSolutionSchema(BaseModel):
    steps: List[SudokuLLMStepSchema]
    final_grid: List[List[int]]
    unique_solution: bool
