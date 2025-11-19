import io
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from typing import Callable, Dict, List, Optional, Sequence
from core.enums.sudoku_simplified_candidate_type import SudokuSimplifiedCandidateType
from core.factories.sudoku_figure_factory import SudokuFigureFactory
from core.sudoku import Sudoku

matplotlib.use("Agg")

class SudokuFigureSerializer:
    def __init__(self, figure: SudokuFigureFactory) -> None:
        self.__figure_factory: SudokuFigureFactory = figure
        self.__candidate_figures: Dict[SudokuSimplifiedCandidateType, Callable[[Sudoku], Sequence[Figure]]] = {
            SudokuSimplifiedCandidateType.ZEROTH_LAYER_NAKED_SINGLES: SudokuFigureFactory.get_naked_singles_sudoku_figures,
            SudokuSimplifiedCandidateType.ZEROTH_LAYER_HIDDEN_SINGLES: SudokuFigureFactory.get_hidden_singles_sudoku_figures,
            SudokuSimplifiedCandidateType.FIRST_LAYER_CONSENSUS: SudokuFigureFactory.get_consensus_sudoku_figures,
        }

    def serialize(self, sudoku: Sudoku, candidate_type: SudokuSimplifiedCandidateType) -> List[bytes]:
        getter: Optional[Callable[[SudokuFigureFactory, Sudoku], Sequence[Figure]]] = self.__candidate_figures.get(candidate_type)
        if getter is None:
            return []

        figures: Sequence[Figure] = getter(self.__figure_factory, sudoku)
        if not figures:
            return []

        payload: List[bytes] = []
        for figure in figures:
            fp = io.BytesIO()
            figure.savefig(fp, format="png", bbox_inches="tight")
            plt.close(figure)
            payload.append(fp.getvalue())
        return payload
