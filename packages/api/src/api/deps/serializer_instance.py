from typing import Optional
from api.deps.factory_instance import FactoryInstance
from api.utils.serializers.sudoku_figure_serializer import SudokuFigureSerializer

class SerializerInstance:
    __sudoku_figure_serializer: Optional[SudokuFigureSerializer] = None

    @classmethod
    def get_sudoku_figure_serializer(cls) -> SudokuFigureSerializer:
        if cls.__sudoku_figure_serializer is None:
            cls.__sudoku_figure_serializer = SudokuFigureSerializer(figure=FactoryInstance.get_sudoku_figure_factory())
        return cls.__sudoku_figure_serializer
