import pytest

from src.sudoku_llm_reasoning.core.sudoku import Sudoku
from src.sudoku_llm_reasoning.core.sudoku_reasoner import SudokuReasoner
from tests.factories.sudoku_factory import SudokuFactory

@pytest.mark.skip()
def test_empty_sudoku_analysis(sudoku_4x4_factory: SudokuFactory, sudoku_reasoner: SudokuReasoner) -> None:
    sudoku: Sudoku = sudoku_4x4_factory.get_empty_sudoku()
    sudoku_reasoner.analyze(sudoku)

@pytest.mark.skip()
def test_naked_singles_sudoku_analysis(sudoku_4x4_factory: SudokuFactory, sudoku_reasoner: SudokuReasoner) -> None:
    sudoku: Sudoku = sudoku_4x4_factory.get_naked_singles_sudoku()
    sudoku_reasoner.analyze(sudoku)

@pytest.mark.skip()
def test_hidden_singles_sudoku_analysis(sudoku_4x4_factory: SudokuFactory, sudoku_reasoner: SudokuReasoner) -> None:
    sudoku: Sudoku = sudoku_4x4_factory.get_hidden_singles_sudoku()
    sudoku_reasoner.analyze(sudoku)

@pytest.mark.skip()
def test_consensus_sudoku_analysis(sudoku_4x4_factory: SudokuFactory, sudoku_reasoner: SudokuReasoner) -> None:
    sudoku: Sudoku = sudoku_4x4_factory.get_consensus_principle_sudoku()
    sudoku_reasoner.analyze(sudoku)
