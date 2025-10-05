from src.sudoku_llm_reasoning.core.sudoku import Sudoku

class SudokuFactory:
    @classmethod
    def get_sudoku(cls) -> Sudoku:
        return Sudoku([
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ])
