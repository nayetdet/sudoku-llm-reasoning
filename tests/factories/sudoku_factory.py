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

    def get_hidden_singles_sudoku(self, prob_zero: float = 0.20) -> Sudoku:
        sudoku: Sudoku = self.get_solved_sudoku()
        grid: List[List[int]] = SudokuUtils.get_grid_copy(sudoku)
        n, b = self.__empty_sudoku.sizes()

        r, c = MatrixUtils.get_random_position(n)
        v = grid[r][c]
        grid[r][c] = 0

        c_candidates = [j for j in range(n) if j != c]
        random.shuffle(c_candidates)
        k = None
        c2 = None
        for j in c_candidates:
            if grid[r][j] != v:
                k = grid[r][j]
                c2 = j
                break
        if k is None:
            return Sudoku(SudokuUtils.get_grid_copy(self.get_solved_sudoku()))

        if grid[r][c2] == k:
            grid[r][c2] = 0

        r_k = next((i for i in range(n) if grid[i][c] == k), None)
        if r_k is not None and r_k != r:
            grid[r_k][c] = 0

        bi = (r // b) * b
        bj = (c // b) * b
        pos_k_block: Tuple[int, int] = None
        for ii in range(bi, bi + b):
            for jj in range(bj, bj + b):
                if grid[ii][jj] == k:
                    pos_k_block = (ii, jj)
                    break
            if pos_k_block is not None:
                break
        if pos_k_block is not None and pos_k_block != (r, c):
            i_b, j_b = pos_k_block
            grid[i_b][j_b] = 0

        positions: List[Tuple[int, int]] = [
            (i, j)
            for i in range(n)
            for j in range(n)
            if grid[i][j] != 0 and grid[i][j] != v and not (i == r and j == c)
        ]
        if positions:
            k_extra = max(0, math.ceil(len(positions) * prob_zero))
            for (i, j) in random.sample(positions, k=min(k_extra, len(positions))):
                grid[i][j] = 0

        return Sudoku(grid)

    def get_consensus_principle_sudoku(self) -> Sudoku:
        raise NotImplementedError()

    def get_unsolvable_sudoku(self) -> Sudoku:
        raise NotImplementedError()
