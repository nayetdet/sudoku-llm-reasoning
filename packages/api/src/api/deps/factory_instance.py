from typing import Dict
from api.config import Config
from api.utils.factories.sudoku_factory import SudokuFactory

class FactoryInstance:
    __sudoku_factories: Dict[int, SudokuFactory] = {}

    @classmethod
    def get_sudoku_factory(cls, n: int) -> SudokuFactory:
        if n not in cls.__sudoku_factories:
            cls.__sudoku_factories[n] = SudokuFactory(n, max_solutions=Config.API.Sudoku.MAX_SOLUTIONS)
        return cls.__sudoku_factories[n]
