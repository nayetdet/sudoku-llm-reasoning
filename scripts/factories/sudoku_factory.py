import random
from typing import Tuple, Optional
from scripts.enums.sudoku_model_candidate_type import SudokuModelCandidateType
from scripts.utils.sudoku_utils import SudokuUtils
from src.sudoku_llm_reasoning.core.sudoku import Sudoku, SudokuCandidate

class SudokuFactory:
    MAX_GENERATION_ATTEMPTS: int = 1000

    def __init__(self, n: int, max_solutions: Optional[int] = None) -> None:
        self.__sudoku: Sudoku = SudokuUtils.get_empty_sudoku(n=n)
        self.__sudoku_solutions: Tuple[Sudoku, ...] = self.__sudoku.solve(max_solutions=max_solutions)

    def get_empty_sudoku(self) -> Sudoku:
        return self.__sudoku

    def get_solved_sudoku(self) -> Sudoku:
        return random.choice(self.__sudoku_solutions)

    def get_sudoku_by_candidate_type(self, candidate_type: SudokuModelCandidateType) -> Optional[Sudoku]:
        for attempt in range(self.MAX_GENERATION_ATTEMPTS):
            sudoku: Sudoku = self.get_solved_sudoku()
            target_removed_cells: int = int((len(sudoku) ** 2) * 0.75)

            for removed_cells in range(target_removed_cells):
                sudoku = SudokuUtils.next_popped_step(sudoku)
                candidates: Optional[Tuple[SudokuCandidate, ...]] = None

                match candidate_type:
                    case SudokuModelCandidateType.ZEROTH_LAYER_NAKED_SINGLES:
                        candidates = sudoku.candidates_0th_layer_naked_singles
                    case SudokuModelCandidateType.ZEROTH_LAYER_HIDDEN_SINGLES:
                        candidates = sudoku.candidates_0th_layer_hidden_singles
                    case SudokuModelCandidateType.FIRST_LAYER_CONSENSUS:
                        candidates = sudoku.candidates_1st_layer_consensus
                        if candidates == sudoku.candidates_1st_layer_partial_consensus:
                            continue

                if candidates:
                    return sudoku

        return None
