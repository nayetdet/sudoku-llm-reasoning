import os
import pytest
from src.sudoku_llm_reasoning.core.sudoku_reasoner import SudokuReasoner
from tests.factories.sudoku_factory import SudokuFactory

@pytest.fixture
def sudoku_4x4_factory() -> SudokuFactory:
    return SudokuFactory(n=4)

@pytest.fixture
def sudoku_9x9_factory() -> SudokuFactory:
    return SudokuFactory(n=9)

@pytest.fixture
def sudoku_reasoner() -> SudokuReasoner:
    llm_model: str = os.getenv("LLM_MODEL")
    llm_api_key: str = os.getenv("LLM_API_KEY")
    return SudokuReasoner(llm_model=llm_model, llm_api_key=llm_api_key)
