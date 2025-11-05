import itertools
import math
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List, Tuple, Set, Dict, Optional
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.text import Text
from core.enums.sudoku_candidate_type import SudokuCandidateType
from core.sudoku import Sudoku, SudokuCandidate

@dataclass(frozen=True)
class SudokuFigureCellColor:
    text_color: Optional[str]
    background_color: Optional[str]

class SudokuFigure:
    def __init__(self, color: str) -> None:
        self.__color: str = color

    def get_naked_singles_sudoku_figures(self, sudoku: Sudoku) -> List[Figure]:
        n, n_isqrt = sudoku.shape()
        figures: List[Figure] = []
        for candidate in sudoku.candidates_0th_layer_naked_singles:
            i, j = candidate.position
            highlighted_positions: Set[Tuple[int, int]] = {
                *[(ii, j) for ii in range(n)],
                *[(i, jj) for jj in range(n)]
            }

            i0, j0 = (i // n_isqrt) * n_isqrt, (j // n_isqrt) * n_isqrt
            highlighted_positions.update(
                (i0 + a, j0 + b)
                for a in range(n_isqrt)
                for b in range(n_isqrt)
            )

            fig, (ax_start, ax_end) = self.__subplots(n, narrows=2)
            self.__plot_sudoku_on_axis(
                ax=ax_start,
                sudoku=sudoku,
                candidate_positions={
                    SudokuCandidateType.ZEROTH_LAYER_NAKED_SINGLES: [
                        candidate.position
                    ]
                },
                colored_positions={
                    SudokuFigureCellColor(text_color=None, background_color=self.__color): list(highlighted_positions)
                }
            )

            self.__plot_next_sudoku_on_axis(ax_end, sudoku=sudoku, sudoku_candidate=candidate)
            figures.append(fig)
        return figures

    def get_hidden_singles_sudoku_figures(self, sudoku: Sudoku) -> List[Figure]:
        n: int = len(sudoku)
        figures: List[Figure] = []
        for candidate in sudoku.candidates_0th_layer_hidden_singles:
            fig, (ax_start, ax_end) = self.__subplots(n, narrows=2)
            self.__plot_sudoku_on_axis(
                ax=ax_start,
                sudoku=sudoku,
                candidate_positions={
                    SudokuCandidateType.ZEROTH_LAYER_PLAIN: [
                        candidate.position
                    ]
                }
            )

            self.__plot_next_sudoku_on_axis(ax_end, sudoku=sudoku, sudoku_candidate=candidate)
            figures.append(fig)
        return figures

    def get_consensus_sudoku_figures(self, sudoku: Sudoku) -> List[Figure]:
        raise NotImplementedError()

    def __plot_next_sudoku_on_axis(self, ax: Axes, sudoku: Sudoku, sudoku_candidate: SudokuCandidate) -> None:
        return self.__plot_sudoku_on_axis(
            ax=ax,
            sudoku=sudoku.next_step_at_position(*sudoku_candidate.position, sudoku_candidate.value),
            colored_positions={
                SudokuFigureCellColor(text_color=self.__color, background_color=None): [
                    sudoku_candidate.position
                ]
            }
        )

    def __plot_sudoku_on_axis(self, ax: Axes, sudoku: Sudoku, candidate_positions: Optional[Dict[SudokuCandidateType, List[Tuple[int, int]]]] = None, colored_positions: Optional[Dict[SudokuFigureCellColor, List[Tuple[int, int]]]] = None) -> None:
        n, n_isqrt = sudoku.shape()
        ax.set_xlim(0, n)
        ax.set_ylim(0, n)
        ax.set_aspect("equal")
        ax.axis("off")

        text_positions: Dict[Tuple[int, int], Text] = {}
        for i, j in itertools.product(range(n), range(n)):
            ax.add_patch(Rectangle((j, n - i - 1), width=1, height=1, fill=False, linewidth=0.75))
            if sudoku.grid[i][j] != 0:
                text: Text = ax.text(j + 0.5, n - i - 0.5, str(sudoku.grid[i][j]), va="center", ha="center", fontsize=18)
                text_positions[(i, j)] = text

        for color_config, positions in (colored_positions or {}).items():
            for (i, j) in positions:
                if color_config.background_color is not None:
                    ax.add_patch(Rectangle((j, n - i - 1), width=1, height=1, facecolor=color_config.background_color, edgecolor=None, alpha=0.35))

                if color_config.text_color and (i, j) in text_positions:
                    text_positions[(i, j)].set_color(color_config.text_color)

        for candidate_type, positions in (candidate_positions or {}).items():
            for (i, j) in positions:
                if sudoku.grid[i][j] != 0:
                    continue

                candidates: Optional[Set[int]] = None
                match candidate_type:
                    case SudokuCandidateType.ZEROTH_LAYER_PLAIN: candidates = sudoku.candidate_values_0th_layer_plain_at_position(i, j)
                    case SudokuCandidateType.ZEROTH_LAYER_NAKED_SINGLES: candidates = sudoku.candidate_values_0th_layer_naked_singles_at_position(i, j)
                    case SudokuCandidateType.ZEROTH_LAYER_HIDDEN_SINGLES: candidates = sudoku.candidate_values_0th_layer_hidden_singles_at_position(i, j)
                    case SudokuCandidateType.ZEROTH_LAYER: candidates = sudoku.candidate_values_0th_layer_at_position(i, j)
                    case SudokuCandidateType.FIRST_LAYER_CONSENSUS: candidates = sudoku.candidate_values_1st_layer_consensus_at_position(i, j)
                    case SudokuCandidateType.NTH_LAYER: candidates = sudoku.candidate_values_nth_layer_at_position(i, j)

                if not candidates:
                    continue

                sorted_candidates: List[int] = sorted(candidates)
                text: str = "\n".join(" ".join(str(x) for x in sorted_candidates[i: i + n_isqrt]) for i in range(0, len(sorted_candidates), n_isqrt))
                ax.text(j + 0.05, n - i - 0.05, text, ha="left", va="top", fontsize=12, color=self.__color)

        for i in range(0, n + 1, n_isqrt):
            ax.plot((0, n), (i, i), linewidth=1.5, color="black")
            ax.plot((i, i), (0, n), linewidth=1.5, color="black")
        ax.add_patch(Rectangle((0, 0), width=n, height=n, fill=False, linewidth=3))

    @classmethod
    def __subplots(cls, n: int, narrows: int) -> Tuple[Figure, Tuple[Axes, Axes, ...]]:
        size: int = math.floor(n * 0.75)
        return plt.subplots(narrows, 1, figsize=(size, size * narrows))

if __name__ == "__main__":
    sf = SudokuFigure(color="red")
    sf.get_naked_singles_sudoku_figures(
        Sudoku(
            grid=[
                [0, 1, 0, 0],
                [2, 0, 0, 1],
                [0, 0, 4, 0],
                [0, 3, 0, 0]
            ]
        )
    )
    plt.show()
