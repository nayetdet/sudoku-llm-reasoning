from typing import Dict, Any
from src.sudoku_llm_reasoning.schemas.sudoku_schemas import NakedSingleCandidateSchema, SudokuCandidatesSchema, SudokuLLMSolutionSchema, SudokuLLMStepSchema

class SudokuMapper:
    @classmethod
    def to_llm_step_schema(cls, data: Dict[str, Any]) -> SudokuLLMStepSchema:
        return SudokuLLMStepSchema(
            step=data.get("step"),
            value=data.get("value"),
            position=data.get("position"),
            candidates_before=data.get("candidates_before"),
            explanation=data.get("explanation")
        )

    @classmethod
    def to_llm_solution_schema(cls, data: Dict[str, Any]) -> SudokuLLMSolutionSchema:
        return SudokuLLMSolutionSchema(
            steps=tuple(cls.to_llm_step_schema(x) for x in data.get("steps")),
            final_grid=data.get("final_grid"),
            unique_solution=data.get("unique_solution")
        )
    
    @classmethod
    def to_llm_candidates_schema(cls, data: Dict[str, Any]) -> NakedSingleCandidateSchema:
        return NakedSingleCandidateSchema(
                        index=data.get("index"),
                        position=data.get("position"),
                        value=data.get("value"),
                        candidates_before=data.get("candidates_before"),
                        explanation=data.get("explanation")
                )
        
    
    @classmethod
    def to_llm_naked_singles_schema(cls, schema: SudokuCandidatesSchema) -> SudokuCandidatesSchema:

        return  SudokuCandidatesSchema(
            candidates=[cls.to_llm_candidates_schema(cand) for cand in schema.get("candidates", [])]
        )