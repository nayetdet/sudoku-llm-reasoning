import textwrap
from src.sudoku_llm_reasoning.deps.llm_instance import LLMInstance
from src.sudoku_llm_reasoning.models.sudoku import Sudoku

class LLMService:
    @classmethod
    def solve_sudoku(cls, sudoku: Sudoku) -> str:
        return LLMInstance.get_llm().generate_content(textwrap.dedent(
            """
            Você é gay?
            """
        ).strip()).text
