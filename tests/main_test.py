from src.sudoku_llm_reasoning.core.sudoku import Sudoku
from src.sudoku_llm_reasoning.core.sudoku_reasoner import SudokuReasoner
from tests.config import Config
from tests.factories.sudoku_factory import SudokuFactory

sudoku_reasoner: SudokuReasoner = SudokuReasoner(
    llm_model=Config.LLM_MODEL,
    llm_api_key=Config.LLM_API_KEY
)

def test_sudoku_analysis():
    sudoku: Sudoku = SudokuFactory.get_sudoku()
    sudoku_reasoner.analyze(sudoku)
