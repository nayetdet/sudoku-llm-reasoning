import math
import itertools
from copy import copy
from dataclasses import dataclass
from typing import List, Tuple, Optional, Set
from z3 import Int, BoolRef, ModelRef, And, Or, Distinct, If, Solver, sat
from src.sudoku_llm_reasoning.enums.sudoku_candidate_type import SudokuCandidateType
from src.sudoku_llm_reasoning.exceptions.sudoku_exceptions import SudokuInvalidDimensionsException

@dataclass(frozen=True)
class SudokuCandidate:
    value: int
    position: Tuple[int, int]

class Sudoku:
    def __init__(self, grid: List[List[int]]) -> None:
        if any(len(row) != len(grid) for row in grid):
            raise SudokuInvalidDimensionsException("Grid must be square")

        if len(grid) != math.isqrt(len(grid)) ** 2:
            raise SudokuInvalidDimensionsException("Grid size must be a perfect square")

        self.__grid: Tuple[Tuple[int, ...], ...] = tuple(tuple(x) for x in grid)
        self.__candidates_0th_layer: Optional[Tuple["SudokuCandidate", ...]] = None
        self.__candidates_0th_layer_naked_singles: Optional[Tuple["SudokuCandidate", ...]] = None
        self.__candidates_0th_layer_hidden_singles: Optional[Tuple["SudokuCandidate", ...]] = None
        self.__candidates_1th_layer: Optional[Tuple["SudokuCandidate", ...]] = None
        self.__candidates_nth_layer: Optional[Tuple["SudokuCandidate", ...]] = None
        self.__solutions: Optional[Tuple["Sudoku", ...]] = None

    @property
    def grid(self) -> Tuple[Tuple[int, ...], ...]:
        return self.__grid

    @property
    def grid_rows(self) -> Tuple[Tuple[int, ...], ...]:
        return self.grid

    @property
    def grid_columns(self) -> Tuple[Tuple[int, ...], ...]:
        n: int = len(self)
        return tuple(tuple(self.grid[i][j] for i in range(n)) for j in range(n))

    @property
    def grid_blocks(self) -> Tuple[Tuple[int, ...], ...]:
        blocks: List[List[int]] = []
        n, n_isqrt = self.sizes()
        for i0, j0 in itertools.product(range(0, n, n_isqrt), range(0, n, n_isqrt)):
            block: List[int] = [self.grid[i0 + i][j0 + j] for i in range(n_isqrt) for j in range(n_isqrt)]
            blocks.append(block)
        return tuple(tuple(x) for x in blocks)

    @property
    def candidates_0th_layer(self) -> Tuple["SudokuCandidate", ...]:
        if self.__candidates_0th_layer is None:
            self.__candidates_0th_layer = self.__solve_all_candidates(candidate_type=SudokuCandidateType.CONSENSUS_0TH_LAYER)
        return self.__candidates_0th_layer

    @property
    def candidates_0th_layer_naked_singles(self) -> Tuple["SudokuCandidate", ...]:
        if self.__candidates_0th_layer_naked_singles is None:
            self.__candidates_0th_layer_naked_singles = self.__solve_all_candidates(candidate_type=SudokuCandidateType.NAKED_SINGLES_0TH_LAYER)
        return self.__candidates_0th_layer_naked_singles

    @property
    def candidates_0th_layer_hidden_singles(self) -> Tuple["SudokuCandidate", ...]:
        if self.__candidates_0th_layer_hidden_singles is None:
            self.__candidates_0th_layer_hidden_singles = self.__solve_all_candidates(candidate_type=SudokuCandidateType.HIDDEN_SINGLES_0TH_LAYER)
        return self.__candidates_0th_layer_hidden_singles

    @property
    def candidates_1th_layer(self) -> Tuple["SudokuCandidate", ...]:
        if self.__candidates_1th_layer is None:
            self.__candidates_1th_layer = self.__solve_all_candidates(candidate_type=SudokuCandidateType.CONSENSUS_1TH_LAYER)
        return self.__candidates_1th_layer

    @property
    def candidates_nth_layer(self) -> Tuple["SudokuCandidate", ...]:
        if self.__candidates_nth_layer is None:
            self.__candidates_nth_layer = self.__solve_all_candidates(candidate_type=SudokuCandidateType.CONSENSUS_NTH_LAYER)
        return self.__candidates_nth_layer

    @property
    def solutions(self) -> Tuple["Sudoku", ...]:
        if self.__solutions is None:
            self.__solutions = self.__solve_all_solutions()
        return self.__solutions

    def __len__(self) -> int:
        return len(self.grid)

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"Sudoku({self.__grid})"

    def sizes(self) -> Tuple[int, int]:
        n: int = len(self)
        return n, math.isqrt(n)

    def is_empty(self) -> bool:
        return all(all(cell == 0 for cell in row) for row in self.grid)

    def is_full(self) -> bool:
        return all(all(cell != 0 for cell in row) for row in self.grid)

    def is_solvable_0th_layer(self) -> bool:
        def has_no_duplicates(cells: Tuple[int, ...]) -> bool:
            nums: List[int] = [x for x in cells if x != 0]
            return len(nums) == len(set(nums))

        are_rows_valid: bool = all(has_no_duplicates(x) for x in self.grid)
        are_columns_valid: bool = all(has_no_duplicates(x) for x in self.grid_columns)
        are_blocks_valid: bool = all(has_no_duplicates(x) for x in self.grid_blocks)
        return are_rows_valid and are_columns_valid and are_blocks_valid

    def is_solvable_nth_layer(self) -> bool:
        return len(self.solutions) > 0

    def is_solved(self) -> bool:
        return self.is_full() and self.is_solvable_nth_layer()

    def next_step_at_position(self, i: int, j: int, value: int) -> "Sudoku":
        grid: List[List[int]] = [list(row) for row in self.grid]
        grid[i][j] = value
        return Sudoku(grid)

    def grid_block_at_position(self, i: int, j: int) -> Tuple[int, ...]:
        n, n_isqrt = self.sizes()
        idx: int = (i // n_isqrt) * n_isqrt + (j // n_isqrt)
        return self.grid_blocks[idx]

    def __candidate_values_0th_layer_at_position(self, i: int, j: int) -> Set[int]:
        if self.grid[i][j] != 0:
            return set()

        n: int = len(self)
        return set(range(1, n + 1)) - (set(self.grid_rows[i]) | set(self.grid_columns[j]) | set(self.grid_block_at_position(i, j))) - {0}

    def __candidate_values_0th_layer_naked_singles_at_position(self, i: int, j: int) -> Set[int]:
        if self.grid[i][j] != 0:
            return set()

        n: int = len(self)
        return set(range(1, n + 1)) - set(self.grid_rows[i]) - set(self.grid_columns[j]) - set(self.grid_block_at_position(i, j))

    def __candidate_values_0th_layer_hidden_singles_at_position(self, i: int, j: int) -> Set[int]:
        n, n_isqrt = self.sizes()
        candidates_grid: List[List[Set[int]]] = [
            [self.__candidate_values_0th_layer_naked_singles_at_position(ii, jj) for jj in range(n)]
            for ii in range(n)
        ]

        i0, j0 = (i // n_isqrt) * n_isqrt, (j // n_isqrt) * n_isqrt
        all_hidden_candidates: Set[int] = {
            x for x in candidates_grid[i][j]
            if (
                not any(x in candidates_grid[i][jj] for jj in range(n) if jj != j)
                or not any(x in candidates_grid[ii][j] for ii in range(n) if ii != i)
                or not any(
                    x in candidates_grid[i0 + ii][j0 + jj]
                    for ii in range(n_isqrt)
                    for jj in range(n_isqrt)
                    if (i0 + ii, j0 + jj) != (i, j)
                )
            )
        }

        return all_hidden_candidates & candidates_grid[i][j]

    def __candidate_values_1th_layer_at_position(self, i: int, j: int) -> Set[int]:
        candidates: Set[int] = self.__candidate_values_0th_layer_at_position(i, j)
        for candidate in copy(candidates):
            next_sudoku: Sudoku = self.next_step_at_position(i, j, candidate)
            if not next_sudoku.is_solvable_0th_layer():
                candidates.remove(candidate)
        return candidates

    def __candidate_values_nth_layer_at_position(self, i: int, j: int) -> Set[int]:
        n: int = len(self)
        candidates: Set[int] = set()
        for candidate in range(1, n + 1):
            next_sudoku: Sudoku = self.next_step_at_position(i, j, candidate)
            if next_sudoku.is_solvable_nth_layer():
                candidates.add(candidate)
        return candidates

    def __solve_all_candidates(self, candidate_type: SudokuCandidateType) -> Tuple["SudokuCandidate", ...]:
        n: int = len(self)
        candidates: List[SudokuCandidate] = []
        for i, j in itertools.product(range(n), range(n)):
            values: Set[int] = set()
            match candidate_type:
                case SudokuCandidateType.NAKED_SINGLES_0TH_LAYER: values = self.__candidate_values_0th_layer_naked_singles_at_position(i, j)
                case SudokuCandidateType.HIDDEN_SINGLES_0TH_LAYER: values = self.__candidate_values_0th_layer_hidden_singles_at_position(i, j)
                case SudokuCandidateType.CONSENSUS_0TH_LAYER: values = self.__candidate_values_0th_layer_at_position(i, j)
                case SudokuCandidateType.CONSENSUS_1TH_LAYER: values = self.__candidate_values_1th_layer_at_position(i, j)
                case SudokuCandidateType.CONSENSUS_NTH_LAYER: values = self.__candidate_values_nth_layer_at_position(i, j)

            for value in values:
                candidates.append(SudokuCandidate(
                    position=(i, j),
                    value=value
                ))
        return tuple(candidates)

    def __solve_all_solutions(self) -> Tuple["Sudoku", ...]:
        # Variables: Integer variable for each cell of the Sudoku grid
        n, n_isqrt = self.sizes()
        cells: List[List[Int]] = [
            [Int(f"x_{i + 1}_{j + 1}") for j in range(n)]
            for i in range(n)
        ]

        # Rule: Each cell must contain a digit (1 to n)
        cell_constraints: List[BoolRef] = [
            And(cells[i][j] >= 1, cells[i][j] <= n)
            for i in range(n)
            for j in range(n)
        ]

        # Rule: Every digit has to be placed exactly once in each row
        row_constraints: List[BoolRef] = [
            Distinct(cells[i])
            for i in range(n)
        ]

        # Rule: Every digit has to be placed exactly once in each row
        column_constraints: List[BoolRef] = [
            Distinct([cells[i][j] for i in range(n)])
            for j in range(n)
        ]

        # Rule: Every digit has to be placed exactly once in each isqrt(n) x isqrt(n) subgrid
        subgrid_constraints: List[BoolRef] = [
            Distinct([cells[i0 + i][j0 + j] for i in range(n_isqrt) for j in range(n_isqrt)])
            for i0 in range(0, n, n_isqrt)
            for j0 in range(0, n, n_isqrt)
        ]

        # Rule: Pre-fill the cells that already have numbers in the given Sudoku grid
        instance_constraints: List[BoolRef] = [
            If(self.grid[i][j] == 0, True, cells[i][j] == self.grid[i][j])
            for i in range(n)
            for j in range(n)
        ]

        solver: Solver = Solver()
        solver.add(cell_constraints + row_constraints + column_constraints + subgrid_constraints + instance_constraints)
        if solver.check() != sat:
            return ()

        solutions: List[Sudoku] = []
        while solver.check() == sat:
            model: ModelRef = solver.model()
            solution_grid: List[List[int]] = [
                [model.evaluate(cells[i][j]).as_long() for j in range(n)]
                for i in range(n)
            ]

            solutions.append(Sudoku(solution_grid))
            solver.add(Or([cells[i][j] != model.evaluate(cells[i][j]) for i in range(n) for j in range(n)]))
        return tuple(solutions)
