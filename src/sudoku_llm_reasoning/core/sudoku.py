import math
import itertools
from typing import List, Tuple, Optional, Set
from z3 import Int, And, Or, Distinct, If, Solver, sat
from src.sudoku_llm_reasoning.exceptions.sudoku_exceptions import SudokuInvalidDimensionsException

class Sudoku:
    def __init__(self, grid: List[List[int]]) -> None:
        if any(len(row) != len(grid) for row in grid):
            raise SudokuInvalidDimensionsException("Grid must be square")

        if len(grid) != math.isqrt(len(grid)) ** 2:
            raise SudokuInvalidDimensionsException("Grid size must be a perfect square")

        self.__grid: Tuple[Tuple[int, ...], ...] = tuple(tuple(row) for row in grid)
        self.__solutions: Optional[List[Sudoku]] = None
        self.__naked_singles: Optional[List[Sudoku]] = None
        self.__hidden_singles: Optional[List[Sudoku]] = None

    def __len__(self) -> int:
        return len(self.__grid)

    def __str__(self) -> str:
        return "\n".join(" ".join(str(num) for num in row) for row in self.__grid)

    def __repr__(self) -> str:
        return f"Sudoku({self.__grid})"

    @property
    def grid(self) -> Tuple[Tuple[int, ...], ...]:
        return self.__grid

    @property
    def solutions(self) -> List["Sudoku"]:
        if self.__solutions is None:
            self.__solutions = self.__solve_all()
        return self.__solutions

    @property
    def naked_singles(self) -> List["Sudoku"]:
        if self.__naked_singles is None:
            self.__naked_singles = self.__solve_all_naked_singles()
        return self.__naked_singles

    @property
    def hidden_singles(self) -> List["Sudoku"]:
        if self.__hidden_singles is None:
            self.__hidden_singles = self.__solve_all_hidden_singles()
        return self.__hidden_singles

    @property
    def singles(self) -> List["Sudoku"]:
        return self.hidden_singles

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

    def naked_candidates(self, i: int, j: int) -> Set[int]:
        if self.__grid[i][j] != 0:
            return set()

        n, n_isqrt = self.sizes()
        row: Set[int] = set(self.__grid[i])
        column: Set[int] = {self.__grid[k][j] for k in range(n)}

        i0 = (i // n_isqrt) * n_isqrt
        j0 = (j // n_isqrt) * n_isqrt
        subgrid: Set[int] = {
            self.__grid[i0 + di][j0 + dj]
            for di in range(n_isqrt)
            for dj in range(n_isqrt)
        }

        return set(range(1, n + 1)) - row - column - subgrid

    def hidden_candidates(self, i: int, j: int) -> Set[int]:
        naked_singles = self.naked_candidates(i, j)
        if not naked_singles:
            return set()

        n, n_isqrt = self.sizes()
        i0 = (i // n_isqrt) * n_isqrt
        j0 = (j // n_isqrt) * n_isqrt

        return {
            x for x in naked_singles
            if (
                all(x not in self.naked_candidates(i, jj) for jj in range(n) if jj != j)
                or all(x not in self.naked_candidates(ii, j) for ii in range(n) if ii != i)
                or all(
                    x not in self.naked_candidates(i0 + di, j0 + dj)
                    for di in range(n_isqrt) for dj in range(n_isqrt)
                    if (i0 + di, j0 + dj) != (i, j)
                )
            )
        }

    def __solve_all(self) -> List["Sudoku"]:
        # Variables: Integer variable for each cell of the Sudoku grid
        n, n_isqrt = self.sizes()
        cells: List[List[Int]] = [
            [Int(f"x_{i + 1}_{j + 1}") for j in range(n)]
            for i in range(n)
        ]

        # Rule: Each cell must contain a digit (1 to n)
        cell_constraints = [
            And(cells[i][j] >= 1, cells[i][j] <= n)
            for i in range(n)
            for j in range(n)
        ]

        # Rule: Every digit has to be placed exactly once in each row
        row_constraints = [
            Distinct(cells[i])
            for i in range(n)
        ]

        # Rule: Every digit has to be placed exactly once in each row
        column_constraints = [
            Distinct([cells[i][j] for i in range(n)])
            for j in range(n)
        ]

        # Rule: Every digit has to be placed exactly once in each isqrt(n) x isqrt(n) subgrid
        subgrid_constraints = [
            Distinct([cells[i0 + i][j0 + j] for i in range(n_isqrt) for j in range(n_isqrt)])
            for i0 in range(0, n, n_isqrt)
            for j0 in range(0, n, n_isqrt)
        ]

        # Rule: Pre-fill the cells that already have numbers in the given Sudoku grid
        instance_constraints = [
            If(self.__grid[i][j] == 0, True, cells[i][j] == self.__grid[i][j])
            for i in range(n)
            for j in range(n)
        ]

        solver = Solver()
        solver.add(cell_constraints + row_constraints + column_constraints + subgrid_constraints + instance_constraints)
        if solver.check() != sat:
            return []

        solutions: List[Sudoku] = []
        while solver.check() == sat:
            model = solver.model()
            solution: List[List[int]] = [
                [model.evaluate(cells[i][j]).as_long() for j in range(n)]
                for i in range(n)
            ]

            solutions.append(Sudoku(solution))
            solver.add(Or([cells[i][j] != model.evaluate(cells[i][j]) for i in range(n) for j in range(n)]))

        return solutions

    def __solve_all_naked_singles(self) -> List["Sudoku"]:
        n: int = len(self)
        naked_singles: List[Sudoku] = []
        for i, j in itertools.product(range(n), range(n)):
            candidates: Set[int] = self.naked_candidates(i, j)
            if len(candidates) == 1:
                grid: List[List[int]] = [list(row) for row in self.__grid]
                grid[i][j] = candidates.pop()
                naked_singles.append(Sudoku(grid))

        return naked_singles

    def __solve_all_hidden_singles(self) -> List["Sudoku"]:
        n: int = len(self)
        hidden_singles: List[Sudoku] = []
        for i, j in itertools.product(range(n), range(n)):
            candidates: Set[int] = self.hidden_candidates(i, j)
            if len(candidates) == 1:
                grid: List[List[int]] = [list(row) for row in self.__grid]
                grid[i][j] = candidates.pop()
                hidden_singles.append(Sudoku(grid))

        return hidden_singles
