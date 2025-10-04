from typing import Dict, Any
from src.sudoku_llm_reasoning.schemas.sudoku_schemas import LLMSudokuSolutionSchema, LLMSudokuStepSchema

class SudokuMapper:
    @classmethod
    def to_llm_step_schema(cls, data: Dict[str, Any]) -> LLMSudokuStepSchema:
        return LLMSudokuStepSchema(
            step=data.get("step"),
            cell=data.get("cell"),
            value=data.get("value"),
            candidates_before=data.get("candidates_before"),
            explanation=data.get("explanation")
        )

    @classmethod
    def to_llm_solution_schema(cls, data: Dict[str, Any]) -> LLMSudokuSolutionSchema:
        return LLMSudokuSolutionSchema(
            steps=[cls.to_llm_step_schema(x) for x in data.get("steps")],
            final_grid=data.get("final_grid"),
            unique_solution=data.get("unique_solution")
        )
