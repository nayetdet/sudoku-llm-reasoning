from typing import Tuple
from packages.core.src.core.schemas.sudoku_llm_candidate_schema import SudokuLLMCandidateSchema
from packages.core.src.core.enums.sudoku_simplified_candidate_type import (
    SudokuSimplifiedCandidateType)

class SudokuCandidateMapper:
    @classmethod
    def to_llm_candidate_schema(cls, value: int, position: Tuple[int, int], candidate_type: SudokuSimplifiedCandidateType, explanation: str) -> SudokuLLMCandidateSchema:
        return SudokuLLMCandidateSchema(
            value=value,
            position=position,
            candidate_type=candidate_type,
            explanation=explanation
        )
