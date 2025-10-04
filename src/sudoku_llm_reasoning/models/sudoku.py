import math
from typing import List, Tuple, Optional
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

    def is_empty(self) -> bool:
        return all(all(cell == 0 for cell in row) for row in self.__grid)

    def is_full(self) -> bool:
        return all(all(cell != 0 for cell in row) for row in self.__grid)

    def is_solvable(self) -> bool:
        return len(self.solutions) > 0

    def is_solved(self) -> bool:
        return self.is_full() and self.is_solvable()

    def __solve_all(self) -> List["Sudoku"]:
        # Variables: Integer variable for each cell of the Sudoku grid
        n: int = len(self.__grid)
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
        n_isqrt: int = math.isqrt(n)
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

sudoku = Sudoku([
    [0, 0, 0, 4],
    [0, 0, 0, 0],
    [2, 0, 0, 3],
    [4, 0, 1, 2]
])
print(sudoku.solutions)
