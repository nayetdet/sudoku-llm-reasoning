import math
import random
import multiprocessing
from concurrent.futures import Future, as_completed
from concurrent.futures.process import ProcessPoolExecutor
from typing import List, Tuple, Optional
from api.config import Config
from api.enums.sudoku_candidate_type import SudokuCandidateType
from api.logger import logger
from api.mappers.sudoku_mapper import SudokuMapper
from api.repositories.sudoku_repository import SudokuRepository
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

    def get_sudokus_by_candidate_type(self, candidate_type: SudokuCandidateType, target_count: int, max_attempts: int) -> List[Sudoku]:
        sudokus: List[Sudoku] = []
        with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
            futures: List[Future[Optional[Sudoku]]] = [
                executor.submit(self.convert_sudoku_grid_into_candidate_type, self.get_solved_sudoku().grid, candidate_type)
                for _ in range(target_count * max_attempts)
            ]

            for future in as_completed(futures):
                sudoku: Optional[Sudoku] = future.result()
                if sudoku is None:
                    logger.info(f"{self.n}x{self.n} grid | {candidate_type.name}: Sudoku generation failed")
                    continue

                if SudokuRepository.create(SudokuMapper.to_sudoku_model(sudoku, candidate_type=candidate_type)):
                    sudokus.append(sudoku)
                    logger.info(f"{self.n}x{self.n} grid | {candidate_type.name}: Sudoku generation succeeded ({len(sudokus)}/{target_count})")
                    if len(sudokus) >= target_count:
                        for f in futures:
                            f.cancel()
                        break
                else: logger.info(f"{self.n}x{self.n} grid | {candidate_type.name}: Sudoku already exists in, skipping")
        if len(sudokus) != target_count:
            logger.warning(f"Could only generate {len(sudokus)}/{target_count} {self.n}x{self.n} grids in for candidate type: {candidate_type.name}")
        return sudokus

    @staticmethod
    def convert_sudoku_grid_into_candidate_type(sudoku_grid: Tuple[Tuple[int, ...], ...], candidate_type: SudokuCandidateType) -> Optional[Sudoku]:
        n: int = len(sudoku_grid)
        sudoku_grid: List[List[int]] = [list(x) for x in sudoku_grid]
        sudoku_grid_positions: List[Tuple[int, int]] = [(i, j) for i in range(n) for j in range(n)]
        random.shuffle(sudoku_grid_positions)

        for removed_cells, (i, j) in enumerate(sudoku_grid_positions):
            sudoku_grid[i][j] = 0
            sudoku = Sudoku(sudoku_grid)
            candidates: Optional[Tuple[SudokuCandidate, ...]] = None

            match candidate_type:
                case SudokuCandidateType.ZEROTH_LAYER_NAKED_SINGLES:
                    min_removed_cells: int = math.ceil(sudoku.area() * Config.API.Sudoku.NAKED_SINGLES_MIN_RATIO)
                    if removed_cells < min_removed_cells or sudoku.candidates_0th_layer_hidden_singles:
                        continue
                    candidates = sudoku.candidates_0th_layer_naked_singles
                case SudokuCandidateType.ZEROTH_LAYER_HIDDEN_SINGLES:
                    if sudoku.candidates_0th_layer_naked_singles:
                        continue
                    candidates = sudoku.candidates_0th_layer_hidden_singles
                case SudokuCandidateType.FIRST_LAYER_CONSENSUS:
                    if sudoku.candidates_0th_layer_naked_singles or sudoku.candidates_0th_layer_hidden_singles:
                        continue
                    candidates = sudoku.candidates_1st_layer_consensus

            if candidates:
                return sudoku
        return None
