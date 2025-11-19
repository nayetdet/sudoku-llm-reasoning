from typing import Dict, Optional
from api.config import Config
from core.factories.sudoku_factory import SudokuFactory
from core.factories.sudoku_figure_factory import SudokuFigureFactory

class FactoryInstance:
    __sudoku_factories: Dict[int, SudokuFactory] = {}
    __sudoku_figure_factory: Optional[SudokuFigureFactory] = None

    @classmethod
    def get_sudoku_factory(cls, n: int) -> SudokuFactory:
        if n not in cls.__sudoku_factories:
            cls.__sudoku_factories[n] = SudokuFactory(n, max_solutions=Config.API.Sudoku.DEFAULT_MAX_SOLUTIONS)
        return cls.__sudoku_factories[n]

    @classmethod
    def get_sudoku_figure_factory(cls) -> SudokuFigureFactory:
        if cls.__sudoku_figure_factory is None:
            cls.__sudoku_figure_factory = SudokuFigureFactory(primary_color="red", secondary_color="darkgreen", tertiary_color="blue")
        return cls.__sudoku_figure_factory
