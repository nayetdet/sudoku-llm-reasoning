import json
from typing import List
from scripts.enums.sudoku_model_candidate_type import SudokuModelCandidateType
from scripts.models import SudokuModel
from src.sudoku_llm_reasoning.core.sudoku import Sudoku

class SudokuMapper:
    @classmethod
    def to_sudoku(cls, sudoku_model: SudokuModel) -> Sudoku:
        grid: List[List[int]] = json.loads(sudoku_model.grid)
        return Sudoku(grid)

    @classmethod
    def to_sudoku_model(cls, sudoku: Sudoku, candidate_type: SudokuModelCandidateType) -> SudokuModel:
        return SudokuModel(
            n=len(sudoku),
            candidate_type=candidate_type,
            grid=json.dumps(sudoku.grid)
        )
