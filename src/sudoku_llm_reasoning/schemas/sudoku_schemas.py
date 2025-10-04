from typing import List
from pydantic import BaseModel

class LLMSudokuStepSchema(BaseModel):
    step: int
    cell: List[int]
    value: int
    candidates_before: List[int]
    explanation: str

class LLMSudokuSolutionSchema(BaseModel):
    steps: List[LLMSudokuStepSchema]
    final_grid: List[List[int]]
    unique_solution: bool
