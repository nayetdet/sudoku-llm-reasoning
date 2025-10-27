import pytest
from src.sudoku_llm_reasoning.core.sudoku_reasoner import SudokuReasoner
from tests.config import Config

@pytest.fixture
def sudoku_reasoner() -> SudokuReasoner:
    return SudokuReasoner(llm_model=Config.LLM.MODEL, llm_api_key=Config.LLM.API_KEY)
