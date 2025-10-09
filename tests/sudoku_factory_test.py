from src.sudoku_llm_reasoning.core.sudoku import Sudoku
from src.sudoku_llm_reasoning.core.sudoku_reasoner import SudokuReasoner
from tests.factories.sudoku_factory import SudokuFactory

NUM_TESTS: int = 1000

def test_naked_singles_sudoku(sudoku_4x4_factory: SudokuFactory, sudoku_reasoner: SudokuReasoner) -> None:
    for _ in range(NUM_TESTS):
        sudoku: Sudoku = sudoku_4x4_factory.get_naked_singles_sudoku(prob_zero=1)
        assert len(sudoku.naked_singles) > 0
