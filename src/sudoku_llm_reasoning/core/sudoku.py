import itertools
import math
from collections import defaultdict
from copy import copy
from dataclasses import dataclass
from typing import List, Tuple, Optional, Set, Dict
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
        self.__candidates_0th_layer_without_inference: Optional[Tuple["SudokuCandidate"], ...] = None
        self.__candidates_0th_layer_naked_singles: Optional[Tuple["SudokuCandidate", ...]] = None
        self.__candidates_0th_layer_hidden_singles: Optional[Tuple["SudokuCandidate", ...]] = None
        self.__candidates_0th_layer: Optional[Tuple["SudokuCandidate", ...]] = None
        self.__candidates_1st_layer_partial_consensus: Optional[Tuple["SudokuCandidate", ...]] = None
        self.__candidates_1st_layer_consensus: Optional[Tuple["SudokuCandidate", ...]] = None
        self.__candidates_nth_layer: Optional[Tuple["SudokuCandidate", ...]] = None
        self.__solutions: Optional[Tuple["Sudoku", ...]] = None

    def __len__(self) -> int:
        return len(self.grid)

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"Sudoku({self.__grid})"

    @property
    def grid(self) -> Tuple[Tuple[int, ...], ...]:
        return self.__grid

    @property
    def grid_columns(self) -> Tuple[Tuple[int, ...], ...]:
        return tuple(zip(*self.grid))

    @property
    def grid_blocks(self) -> Tuple[Tuple[int, ...], ...]:
        blocks: List[List[int]] = []
        n, n_isqrt = self.sizes()
        for i0, j0 in itertools.product(range(0, n, n_isqrt), range(0, n, n_isqrt)):
            block: List[int] = [self.grid[i0 + i][j0 + j] for i in range(n_isqrt) for j in range(n_isqrt)]
            blocks.append(block)
        return tuple(tuple(x) for x in blocks)

    @property
    def grid_rows_with_positions(self) -> Tuple[Tuple[Tuple[int, Tuple[int,int]], ...], ...]:
        return tuple(
            tuple((value, (i, j)) for j, value in enumerate(row))
            for i, row in enumerate(self.grid)
        )

    @property
    def grid_columns_with_positions(self) -> Tuple[Tuple[Tuple[int, Tuple[int,int]], ...], ...]:
        n: int = len(self.grid)
        return tuple(
            tuple((self.grid[i][j], (i, j)) for i in range(n))
            for j in range(n)
        )

    @property
    def grid_blocks_with_positions(self) -> Tuple[Tuple[Tuple[int, Tuple[int,int]], ...], ...]:
        blocks: List[Tuple[Tuple[int, Tuple[int,int]], ...]] = []
        n, n_isqrt = self.sizes()
        for i0, j0 in itertools.product(range(0, n, n_isqrt), range(0, n, n_isqrt)):
            block: Tuple[Tuple[int, Tuple[int,int]], ...] = tuple(
                (self.grid[i0 + i][j0 + j], (i0 + i, j0 + j))
                for i in range(n_isqrt)
                for j in range(n_isqrt)
            )
            blocks.append(block)
        return tuple(blocks)

    @property
    def candidates_0th_layer_without_inference(self) -> Tuple["SudokuCandidate", ...]:
        if self.__candidates_0th_layer_without_inference is None:
            self.__candidates_0th_layer_without_inference = self.__solve_all_candidates(candidate_type=SudokuCandidateType.ZEROTH_LAYER_WITHOUT_INFERENCE)
        return self.__candidates_0th_layer_without_inference

    @property
    def candidates_0th_layer_naked_singles(self) -> Tuple["SudokuCandidate", ...]:
        if self.__candidates_0th_layer_naked_singles is None:
            self.__candidates_0th_layer_naked_singles = self.__solve_all_candidates(candidate_type=SudokuCandidateType.ZEROTH_LAYER_NAKED_SINGLES)
        return self.__candidates_0th_layer_naked_singles

    @property
    def candidates_0th_layer_hidden_singles(self) -> Tuple["SudokuCandidate", ...]:
        if self.__candidates_0th_layer_hidden_singles is None:
            self.__candidates_0th_layer_hidden_singles = self.__solve_all_candidates(candidate_type=SudokuCandidateType.ZEROTH_LAYER_HIDDEN_SINGLES)
        return self.__candidates_0th_layer_hidden_singles

    @property
    def candidates_0th_layer(self) -> Tuple["SudokuCandidate", ...]:
        if self.__candidates_0th_layer is None:
            self.__candidates_0th_layer = self.__solve_all_candidates(candidate_type=SudokuCandidateType.ZEROTH_LAYER)
        return self.__candidates_0th_layer

    @property
    def candidates_1st_layer_partial_consensus(self) -> Tuple["SudokuCandidate", ...]:
        if self.__candidates_1st_layer_partial_consensus is None:
            self.__candidates_1st_layer_partial_consensus = self.__solve_all_candidates(candidate_type=SudokuCandidateType.FIRST_LAYER_PARTIAL_CONSENSUS)
        return self.__candidates_1st_layer_partial_consensus

    @property
    def candidates_1st_layer_consensus(self) -> Tuple["SudokuCandidate", ...]:
        if self.__candidates_1st_layer_consensus is None:
            self.__candidates_1st_layer_consensus = self.__solve_all_candidates(candidate_type=SudokuCandidateType.FIRST_LAYER_CONSENSUS)
        return self.__candidates_1st_layer_consensus

    @property
    def candidates_nth_layer(self) -> Tuple["SudokuCandidate", ...]:
        if self.__candidates_nth_layer is None:
            self.__candidates_nth_layer = self.__solve_all_candidates(candidate_type=SudokuCandidateType.NTH_LAYER)
        return self.__candidates_nth_layer

    @property
    def solutions(self) -> Tuple["Sudoku", ...]:
        if self.__solutions is None:
            self.__solutions = self.__solve_all_solutions()
        return self.__solutions

    def grid_block_at_position(self, i: int, j: int) -> Tuple[int, ...]:
        n, n_isqrt = self.sizes()
        ii: int = (i // n_isqrt) * n_isqrt + (j // n_isqrt)
        return self.grid_blocks[ii]

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

        return (
            all(has_no_duplicates(x) for x in self.grid)
            and all(has_no_duplicates(x) for x in self.grid_columns)
            and all(has_no_duplicates(x) for x in self.grid_blocks)
        )

    def is_solvable_nth_layer(self) -> bool:
        return len(self.solutions) > 0

    def is_solved(self) -> bool:
        return self.is_full() and self.is_solvable_nth_layer()

    def next_step_at_position(self, i: int, j: int, value: int) -> "Sudoku":
        grid: List[List[int]] = [list(row) for row in self.grid]
        grid[i][j] = value
        return Sudoku(grid)

    def candidate_values_0th_layer_without_inference_at_position(self, i: int, j: int) -> Set[int]:
        if self.grid[i][j] != 0:
            return set()

        n: int = len(self)
        return set(range(1, n + 1)) - (set(self.grid[i]) | set(self.grid_columns[j]) | set(self.grid_block_at_position(i, j))) - {0}

    def candidate_values_0th_layer_naked_singles_at_position(self, i: int, j: int) -> Set[int]:
        if self.grid[i][j] != 0:
            return set()

        n: int = len(self)
        candidates: Set[int] = set(range(1, n + 1)) - set(self.grid[i]) - set(self.grid_columns[j]) - set(self.grid_block_at_position(i, j)) - {0}
        return candidates if len(candidates) == 1 else set()

    def candidate_values_0th_layer_hidden_singles_at_position(self, i: int, j: int) -> Set[int]:
        if self.grid[i][j] != 0:
            return set()

        n, n_isqrt = self.sizes()
        base_candidates_grid: List[List[Set[int]]] = [
            [
                self.candidate_values_0th_layer_without_inference_at_position(ii, jj)
                for jj in range(n)
            ]
            for ii in range(n)
        ]

        i0, j0 = (i // n_isqrt) * n_isqrt, (j // n_isqrt) * n_isqrt
        candidates: Set[int] = set()
        for x in base_candidates_grid[i][j]:
            is_unique_in_row: bool = not any(x in base_candidates_grid[i][jj] for jj in range(n) if jj != j)
            is_unique_in_column: bool = not any(x in base_candidates_grid[ii][j] for ii in range(n) if ii != i)
            is_unique_in_block: bool = not any(
                x in base_candidates_grid[i0 + ii][j0 + jj]
                for ii in range(n_isqrt)
                for jj in range(n_isqrt)
                if (i0 + ii, j0 + jj) != (i, j)
            )

            if is_unique_in_row or is_unique_in_column or is_unique_in_block:
                candidates.add(x)

        return candidates if len(candidates) == 1 else set()

    def candidate_values_0th_layer_at_position(self, i: int, j: int) -> Set[int]:
        if self.grid[i][j] != 0:
            return set()

        base_candidates: Set[int] = self.candidate_values_0th_layer_without_inference_at_position(i, j)
        naked_candidates: Set[int] = self.candidate_values_0th_layer_naked_singles_at_position(i, j)
        hidden_candidates: Set[int] = self.candidate_values_0th_layer_hidden_singles_at_position(i, j)
        return base_candidates if not naked_candidates and not hidden_candidates else naked_candidates | hidden_candidates

    def candidate_values_1st_layer_partial_consensus_at_position(self, i: int, j: int) -> Set[int]:
        if self.grid[i][j] != 0:
            return set()

        candidates: Set[int] = self.candidate_values_0th_layer_at_position(i, j)
        for candidate in copy(candidates):
            next_sudoku: Sudoku = self.next_step_at_position(i, j, candidate)
            if not next_sudoku.is_solvable_0th_layer():
                candidates.remove(candidate)
        return candidates

    def candidate_values_1st_layer_consensus_at_position(self, i: int, j: int) -> Set[int]:
        if self.grid[i][j] != 0:
            return set()

        n: int = len(self)
        candidates: Set[int] = set()
        for region in self.grid_rows_with_positions + self.grid_columns_with_positions + self.grid_blocks_with_positions:
            candidate_positions: Dict[int, List[Tuple[int, int]]] = defaultdict(list)
            for value, position in region:
                if value != 0:
                    continue

                partial_candidates: Set[int] = self.candidate_values_1st_layer_partial_consensus_at_position(*position)
                for candidate in partial_candidates:
                    candidate_positions[candidate].append(position)

            for candidate, positions in candidate_positions.items():
                inner_candidates: List[int] = []
                for ii, jj in positions:
                    next_sudoku: Sudoku = self.next_step_at_position(ii, jj, candidate)
                    while True:
                        single_candidates: List[Tuple[int, int, int]] = [
                            (iii, jjj, next(iter(cell_candidates)))
                            for iii, jjj in itertools.product(range(n), range(n))
                            if (
                                (iii, jjj) != (i, j)
                                and next_sudoku.grid[iii][jjj] == 0
                                and len((cell_candidates := next_sudoku.candidate_values_0th_layer_at_position(iii, jjj))) == 1
                            )
                        ]

                        if not single_candidates:
                            break

                        for iii, jjj, single_candidate in single_candidates:
                            next_sudoku = next_sudoku.next_step_at_position(iii, jjj, single_candidate)

                    next_candidates: Set[int] = next_sudoku.candidate_values_0th_layer_at_position(i, j)
                    if len(next_candidates) == 1:
                        inner_candidates.append(next(iter(next_candidates)))

                if len(inner_candidates) == len(positions) and len(set(inner_candidates)) == 1:
                    candidates.add(next(iter(inner_candidates)))

        base_candidates: Set[int] = self.candidate_values_1st_layer_partial_consensus_at_position(i, j)
        return candidates if candidates else base_candidates

    def candidate_values_nth_layer_at_position(self, i: int, j: int) -> Set[int]:
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
                case SudokuCandidateType.ZEROTH_LAYER_WITHOUT_INFERENCE: values = self.candidate_values_0th_layer_without_inference_at_position(i, j)
                case SudokuCandidateType.ZEROTH_LAYER_NAKED_SINGLES: values = self.candidate_values_0th_layer_naked_singles_at_position(i, j)
                case SudokuCandidateType.ZEROTH_LAYER_HIDDEN_SINGLES: values = self.candidate_values_0th_layer_hidden_singles_at_position(i, j)
                case SudokuCandidateType.ZEROTH_LAYER: values = self.candidate_values_0th_layer_at_position(i, j)
                case SudokuCandidateType.FIRST_LAYER_PARTIAL_CONSENSUS: values = self.candidate_values_1st_layer_partial_consensus_at_position(i, j)
                case SudokuCandidateType.FIRST_LAYER_CONSENSUS: values = self.candidate_values_1st_layer_consensus_at_position(i, j)
                case SudokuCandidateType.NTH_LAYER: values = self.candidate_values_nth_layer_at_position(i, j)

            for value in values:
                candidates.append(
                    SudokuCandidate(
                        position=(i, j),
                        value=value
                    )
                )

        return tuple(candidates)

    def __solve_all_solutions(self) -> Tuple["Sudoku", ...]:
        # Variables: Integer variable for each cell of the Sudoku grid
        n, n_isqrt = self.sizes()
        cells: List[List[Int]] = [
            [
                Int(f"x_{i + 1}_{j + 1}")
                for j in range(n)
            ]
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
            Distinct(
                [
                    cells[i][j]
                    for i in range(n)
                ]
            )
            for j in range(n)
        ]

        # Rule: Every digit has to be placed exactly once in each isqrt(n) x isqrt(n) subgrid
        subgrid_constraints: List[BoolRef] = [
            Distinct(
                [
                    cells[i0 + i][j0 + j]
                    for i in range(n_isqrt)
                    for j in range(n_isqrt)
                ]
            )
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
                [
                    model.evaluate(cells[i][j]).as_long()
                    for j in range(n)
                ]
                for i in range(n)
            ]

            solutions.append(Sudoku(solution_grid))
            solver.add(
                Or(
                    [
                        cells[i][j] != model.evaluate(cells[i][j])
                        for i in range(n)
                        for j in range(n)
                    ]
                )
            )

        return tuple(solutions)
