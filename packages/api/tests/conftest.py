import pytest
from api.config import Config
from core.sudoku_reasoner import SudokuReasoner

@pytest.fixture
def sudoku_reasoner() -> SudokuReasoner:
    return SudokuReasoner(llm_model=Config.LLM.MODEL, llm_api_key=Config.LLM.API_KEY)
