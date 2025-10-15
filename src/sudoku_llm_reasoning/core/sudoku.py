import math
import itertools
from dataclasses import dataclass
from typing import List, Tuple, Optional, Set
from z3 import Int, BoolRef, ModelRef, And, Or, Distinct, If, Solver, sat
#from sudoku_llm_reasoning.exceptions.sudoku_exceptions import SudokuInvalidDimensionsException
from ..exceptions.sudoku_exceptions import SudokuInvalidDimensionsException


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

    
    def _column_values(self, j: int) -> Set[int]:
        n = len(self)
        return {self.grid[i][j] for i in range(n) if self.grid[i][j] != 0}
    
    def _row_values(self, i: int) -> Set[int]:
        n = len(self)
        return {self.grid[i][j] for j in range(n) if self.grid[i][j] != 0}
    
    def _is_valid_candidate(self, i: int, j: int, val: int) -> bool:
        """
        Retorna True se val PODE ser colocado em (i, j) sem violar
        linha, coluna ou sub-bloco. False caso contrário.
        """
        n, n_isqrt = self.sizes()

        # verifica linha
        if val in self._row_values(i):
            return False

        # verifica coluna
        if val in self._column_values(j):
            return False

        # verifica sub-bloco
        i0, j0 = (i // n_isqrt) * n_isqrt, (j // n_isqrt) * n_isqrt
        for ii in range(n_isqrt):
            for jj in range(n_isqrt):
                if self.grid[i0 + ii][j0 + jj] == val:
                    return False

        return True

    def _block_sudoku_singles(self, i: int, j: int) -> list[SudokuSingle]:
        n, n_isqrt = self.sizes()
        i0, j0 = (i // n_isqrt) * n_isqrt, (j // n_isqrt) * n_isqrt
        return [SudokuSingle(position=(i0 + ii, j0 + jj), value=self.grid[i0 + ii][j0 + jj]) for ii in range(n_isqrt) for jj in range(n_isqrt) if self.grid[i0 + ii][j0 + jj] == 0 and not (i0 + ii == i and j0 + jj == j)]

    def find_consensus_candidates(self) -> List[SudokuSingle]:
        n = len(self)
        consensus: List[SudokuSingle] = []

        for i in range(n):
            for j in range(n):
                if self.grid[i][j] != 0:
                    continue

                possible_value: Optional[SudokuSingle] = None

                for val in range(1, n + 1):
                    # primeiro teste rápido (linha/coluna via comparação com candidate)
                    if not self._is_valid_candidate(i, j, val):
                        continue
                
                    sup_candidate = self.next_step(i, j, val)

                    absurd_values: List[SudokuSingle] = []
                    # pegar os vizinhos no bloco já no candidato (onde (i,j) está preenchido)
                    neighbor_singles = self._block_sudoku_singles(i, j)

                    for neighbor in neighbor_singles:
                        ni, nj = neighbor.position
                        # cheque se o valor do candidate permanece válido no vizinho
                        # se NÃO for válido (i.e., criou contradição), é absurdo
                        if not self._is_valid_candidate(ni, nj, val):
                            absurd_values.append(neighbor)
                            break  # basta um absurd para invalidar este val
                            
                    if not absurd_values:
                        possible_value = SudokuSingle(position=(i, j), value=val)
                        break  # opcional: parar após encontrar um candidato consensual
                    absurd_values.clear()
                if possible_value is not None:
                    consensus.append(possible_value)

        return consensus



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


if __name__ == "__main__":
    grid = [
        [5, 3, 0,  0, 7, 0,  0, 0, 0],
        [6, 0, 0,  1, 9, 5,  0, 0, 0],
        [0, 9, 8,  0, 0, 0,  0, 6, 0],

        [8, 0, 0,  0, 6, 0,  0, 0, 3],
        [4, 0, 0,  8, 0, 3,  0, 0, 1],
        [7, 0, 0,  0, 2, 0,  0, 0, 6],

        [0, 6, 0,  0, 0, 0,  2, 8, 0],
        [0, 0, 0,  4, 1, 9,  0, 0, 5],
        [0, 0, 0,  0, 8, 0,  0, 7, 9]
    ]

    sudolu = Sudoku(grid)
    print(sudolu)
    # print("Is empty:", sudolu.is_empty())
    # print("Is full:", sudolu.is_full())
    # print("Is solvable:", sudolu.is_solvable())
    # print("Is solved:", sudolu.is_solved())
    # print("Naked singles:", sudolu.naked_singles)
    # print("Hidden singles:", sudolu.hidden_singles)
    print("Consensus:", [cell for cell in sudolu.find_consensus_candidates()])
    print("Solutions:")
    for solution in sudolu.solutions:
        print(solution)
