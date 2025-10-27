from typing import List
from scripts.utils.matrix_utils import MatrixUtils
from src.sudoku_llm_reasoning.core.sudoku import Sudoku

class SudokuUtils:
    @classmethod
    def get_empty_sudoku(cls, n: int) -> Sudoku:
        return Sudoku(MatrixUtils.get_empty_matrix(n))

    @classmethod
    def next_popped_step(cls, sudoku: Sudoku) -> Sudoku:
        i, j = MatrixUtils.get_random_position(len(sudoku))
        sudoku_grid: List[List[int]] = [list(x) for x in sudoku.grid]
        sudoku_grid[i][j] = 0
        return Sudoku(sudoku_grid)
