import math
import itertools
from dataclasses import dataclass
from typing import List, Tuple, Optional, Set
from z3 import Int, BoolRef, ModelRef, And, Or, Distinct, If, Solver, sat
from src.sudoku_llm_reasoning.exceptions.sudoku_exceptions import SudokuInvalidDimensionsException

@dataclass
class SudokuSingle:
    value: int
    position: Tuple[int, int]

class Sudoku:
    def __init__(self, grid: List[List[int]]) -> None:
        if any(len(row) != len(grid) for row in grid):
            raise SudokuInvalidDimensionsException("Grid must be square")

        if len(grid) != math.isqrt(len(grid)) ** 2:
            raise SudokuInvalidDimensionsException("Grid size must be a perfect square")

        self.__grid: Tuple[Tuple[int, ...], ...] = tuple(tuple(row) for row in grid)
        self.__solutions: Optional[Tuple[Sudoku, ...]] = None
        self.__naked_singles: Optional[Tuple[SudokuSingle, ...]] = None
        self.__hidden_singles: Optional[Tuple[SudokuSingle, ...]] = None

    def __len__(self) -> int:
        return len(self.__grid)

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"Sudoku({self.__grid})"

    @property
    def grid(self) -> Tuple[Tuple[int, ...], ...]:
        return self.__grid

    @property
    def solutions(self) -> Tuple["Sudoku", ...]:
        if self.__solutions is None:
            self.__solutions = self.__solve_all()
        return self.__solutions

    @property
    def naked_singles(self) -> Tuple[SudokuSingle, ...]:
        if self.__naked_singles is None:
            self.__naked_singles = self.__solve_all_singles(hidden=False)
        return self.__naked_singles

    @property
    def hidden_singles(self) -> Tuple[SudokuSingle, ...]:
        if self.__hidden_singles is None:
            self.__hidden_singles = self.__solve_all_singles(hidden=True)
        return self.__hidden_singles

    def sizes(self) -> Tuple[int, int]:
        n: int = len(self)
        return n, math.isqrt(n)

    def is_empty(self) -> bool:
        return all(all(cell == 0 for cell in row) for row in self.__grid)

    def is_full(self) -> bool:
        return all(all(cell != 0 for cell in row) for row in self.__grid)

    def is_solvable(self) -> bool:
        return len(self.solutions) > 0

    def is_solved(self) -> bool:
        return self.is_full() and self.is_solvable()

    def next_step(self, i: int, j: int, value: int) -> "Sudoku":
        grid: List[List[int]] = [list(row) for row in self.__grid]
        grid[i][j] = value
        return Sudoku(grid)

    def naked_candidates(self, i: int, j: int) -> Set[int]:
        if self.__grid[i][j] != 0:
            return set()

        n, n_isqrt = self.sizes()
        row: Set[int] = set(self.__grid[i])
        column: Set[int] = {self.__grid[k][j] for k in range(n)}

        i0, j0 = (i // n_isqrt) * n_isqrt, (j // n_isqrt) * n_isqrt
        subgrid: Set[int] = {
            self.__grid[i0 + ii][j0 + jj]
            for ii in range(n_isqrt)
            for jj in range(n_isqrt)
        }

        return set(range(1, n + 1)) - row - column - subgrid

    def hidden_candidates(self, i: int, j: int) -> Set[int]:
        n, n_isqrt = self.sizes()
        i0, j0 = (i // n_isqrt) * n_isqrt, (j // n_isqrt) * n_isqrt
        candidates_grid: List[List[Set[int]]] = [
            [self.naked_candidates(ii, jj) for jj in range(n)]
            for ii in range(n)
        ]

        return {
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

    def __solve_all(self) -> Tuple["Sudoku", ...]:
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
            If(self.__grid[i][j] == 0, True, cells[i][j] == self.__grid[i][j])
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

    def __solve_all_singles(self, hidden: bool = True) -> Tuple[SudokuSingle, ...]:
        n: int = len(self)
        singles: List[SudokuSingle] = []
        for i, j in itertools.product(range(n), range(n)):
            candidates: Set[int] = self.hidden_candidates(i, j) if hidden else self.naked_candidates(i, j)
            if len(candidates) == 1:
                singles.append(SudokuSingle(position=(i, j), value=candidates.pop()))
        return tuple(singles)
