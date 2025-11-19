import math
import random
import multiprocessing
from concurrent.futures import Future, as_completed
from concurrent.futures.process import ProcessPoolExecutor
from typing import List, Tuple, Optional, Iterator
from core.enums.sudoku_simplified_candidate_type import SudokuSimplifiedCandidateType
from core.sudoku import Sudoku, SudokuCandidate

class SudokuFactory:
    def __init__(self, n: int, max_solutions: Optional[int] = None) -> None:
        self.__sudoku: Sudoku = Sudoku(grid=[[0 for _ in range(n)] for _ in range(n)])
        self.__sudoku_solutions: Tuple[Sudoku, ...] = self.__sudoku.solve(max_solutions=max_solutions)

    @property
    def n(self) -> int:
        return len(self.__sudoku)

    def get_empty_sudoku(self) -> Sudoku:
        return self.__sudoku

    def get_solved_sudoku(self) -> Sudoku:
        return random.choice(self.__sudoku_solutions)

    def get_sudokus_by_candidate_type(self, candidate_type: SudokuSimplifiedCandidateType, target_count: int, max_attempts: int) -> Iterator[Optional[Sudoku]]:
        with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
            futures: List[Future[Optional[Sudoku]]] = [
                executor.submit(self.convert_sudoku_grid_into_candidate_type, self.get_solved_sudoku().grid, candidate_type)
                for _ in range(target_count * max_attempts)
            ]

            for future in as_completed(futures):
                yield future.result()

    @staticmethod
    def convert_sudoku_grid_into_candidate_type(sudoku_grid: Tuple[Tuple[int, ...], ...], candidate_type: SudokuSimplifiedCandidateType) -> Optional[Sudoku]:
        n: int = len(sudoku_grid)
        sudoku_grid: List[List[int]] = [list(x) for x in sudoku_grid]
        sudoku_grid_positions: List[Tuple[int, int]] = [(i, j) for i in range(n) for j in range(n)]
        random.shuffle(sudoku_grid_positions)

        for removed_cells, (i, j) in enumerate(sudoku_grid_positions):
            sudoku_grid[i][j] = 0
            sudoku = Sudoku(sudoku_grid)
            candidates: Optional[Tuple[SudokuCandidate, ...]] = None

            match candidate_type:
                case SudokuSimplifiedCandidateType.ZEROTH_LAYER_NAKED_SINGLES:
                    min_removed_cells: int = math.ceil(sudoku.area() * 0.25)
                    if removed_cells < min_removed_cells or sudoku.candidates_0th_layer_hidden_singles:
                        continue
                    candidates = sudoku.candidates_0th_layer_naked_singles
                case SudokuSimplifiedCandidateType.ZEROTH_LAYER_HIDDEN_SINGLES:
                    if sudoku.candidates_0th_layer_naked_singles:
                        continue
                    candidates = sudoku.candidates_0th_layer_hidden_singles
                case SudokuSimplifiedCandidateType.FIRST_LAYER_CONSENSUS:
                    if sudoku.candidates_0th_layer_naked_singles or sudoku.candidates_0th_layer_hidden_singles:
                        continue
                    candidates = sudoku.candidates_1st_layer_consensus

            if candidates:
                return sudoku
        return None
