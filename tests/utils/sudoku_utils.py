from typing import List
from src.sudoku_llm_reasoning.core.sudoku import Sudoku

class SudokuUtils:
    @classmethod
    def get_grid_copy(cls, sudoku: Sudoku) -> List[List[int]]:
        return [list(row) for row in sudoku.grid]
