import math
from typing import List, Optional
from z3 import Int, And, Distinct, If, Solver, sat
from src.sudoku_llm_reasoning.exceptions.sudoku_exceptions import SudokuInvalidDimensionException

class Sudoku:
    def __init__(self, n: int) -> None:
        if n != math.isqrt(n) ** 2:
            raise SudokuInvalidDimensionException()

        self.__n: int = n
        self.__grid: List[List[int]] = []

    def __str__(self) -> str:
        return "\n".join(" ".join(str(num) for num in row) for row in self.__grid)

    def solve(self) -> Optional[List[List[int]]]:
        # Variables: Integer variable for each cell of the Sudoku grid
        cells: List[List[Int]] = [
            [Int(f"x_{i + 1}_{j + 1}") for j in range(self.__n)]
            for i in range(self.__n)
        ]

        # Rule: Each cell must contain a digit (1 to n)
        cell_constraints = [
            And(cells[i][j] >= 1, cells[i][j] <= self.__n)
            for i in range(self.__n)
            for j in range(self.__n)
        ]

        # Rule: Every digit has to be placed exactly once in each row
        row_constraints = [
            Distinct(cells[i])
            for i in range(self.__n)
        ]

        # Rule: Every digit has to be placed exactly once in each row
        column_constraints = [
            Distinct([cells[i][j] for i in range(self.__n)])
            for j in range(self.__n)
        ]

        # Rule: Every digit has to be placed exactly once in each isqrt(n) x isqrt(n) subgrid
        n_root: int = math.isqrt(self.__n)
        subgrid_constraints = [
            Distinct([cells[i + i0][j + j0]] for i in range(i0) for j in range(j0))
            for i0 in range(0, self.__n, n_root)
            for j0 in range(0, self.__n, n_root)
        ]

        # Rule: Pre-fill the cells that already have numbers in the given Sudoku grid
        instance_constraints = [
            If(self.__grid[i][j] == 0, True, cells[i][j] == self.__grid[i][j])
            for i in range(self.__n)
            for j in range(self.__n)
        ]

        solver = Solver()
        solver.add(cell_constraints + row_constraints + column_constraints + subgrid_constraints + instance_constraints)
        if solver.check() != sat:
            return None

        model = solver.model()
        return [
            [int(str(model.evaluate(cells[i][j]))) for j in range(self.__n)]
            for i in range(self.__n)
        ]
