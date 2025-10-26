import math
import random
from typing import List, Tuple
from src.sudoku_llm_reasoning.core.sudoku import Sudoku
from tests.utils.matrix_utils import MatrixUtils
from tests.utils.sudoku_utils import SudokuUtils

class SudokuFactory:
    def __init__(self, n: int) -> None:
        self.__empty_sudoku: Sudoku = Sudoku(MatrixUtils.get_empty_matrix(n))

    def get_empty_sudoku(self) -> Sudoku:
        return self.__empty_sudoku

    def get_solved_sudoku(self) -> Sudoku:
        return random.choice(self.__empty_sudoku.solutions)

    def get_naked_singles_sudoku(self, prob_zero: float = 0.30) -> Sudoku:
        sudoku: Sudoku = self.get_solved_sudoku()
        sudoku_grid: List[List[int]] = SudokuUtils.get_grid_copy(sudoku)
        n, n_isqrt = self.__empty_sudoku.sizes()

        row_idx, col_idx = MatrixUtils.get_random_position(n)
        sudoku_grid[row_idx][col_idx] = 0

        preserve_type: str = random.choice(["row", "column", "block"])
        if preserve_type == "row": positions: List[Tuple[int, int]] = [(i, j) for i in range(n) if i != row_idx for j in range(n)]
        elif preserve_type == "column": positions: List[Tuple[int, int]] = [(i, j) for i in range(n) for j in range(n) if j != col_idx]
        else:
            i0, j0 = (row_idx // n_isqrt) * n_isqrt, (col_idx // n_isqrt) * n_isqrt
            subgrid_positions: List[Tuple[int, int]] = [(i0 + i, j0 + j) for i in range(n_isqrt) for j in range(n_isqrt)]
            positions: List[Tuple[int, int]] = [(i, j) for i in range(n) for j in range(n) if (i, j) not in subgrid_positions]

        for i, j in random.sample(positions, k=max(1, math.ceil(len(positions) * prob_zero))):
            sudoku_grid[i][j] = 0

        return Sudoku(sudoku_grid)

    def get_hidden_singles_sudoku(self) -> Sudoku:
        sudoku: Sudoku = self.get_solved_sudoku()
        sudoku_grid: List[List[int]] = SudokuUtils.get_grid_copy(sudoku)
        n, n_isqrt = self.__empty_sudoku.sizes()

        row_idx, col_idx = MatrixUtils.get_random_position(n)
        d = sudoku_grid[row_idx][col_idx]

        preserve_type = random.choice(["row", "column", "block"])
        if preserve_type == "row": unit_positions: List[Tuple[int, int]] = [(row_idx, j) for j in range(n)]
        elif preserve_type == "column": unit_positions = [(i, col_idx) for i in range(n)]
        else:
            i0 = (row_idx // n_isqrt) * n_isqrt
            j0 = (col_idx // n_isqrt) * n_isqrt
            unit_positions = [(i0 + i, j0 + j) for i in range(n_isqrt) for j in range(n_isqrt)]

        sudoku_grid[row_idx][col_idx] = 0
        candidates_in_unit = [(i, j) for (i, j) in unit_positions if not (i == row_idx and j == col_idx) and sudoku_grid[i][j] != d]
        k_in_unit = max(1, min(len(candidates_in_unit), n_isqrt))
        for (i, j) in random.sample(candidates_in_unit, k=k_in_unit):
            sudoku_grid[i][j] = 0

        return Sudoku(sudoku_grid)

    def get_partial_consensus_sudoku(self) -> Sudoku:
        raise NotImplementedError()

    def get_consensus_sudoku(self) -> Sudoku:
        raise NotImplementedError()
