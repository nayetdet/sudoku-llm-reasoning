import itertools
import math
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List, Tuple, Set, Dict, Optional
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle, FancyArrowPatch, Circle
from matplotlib.text import Text
from core.enums.sudoku_candidate_type import SudokuCandidateType
from core.sudoku import Sudoku, SudokuCandidate

@dataclass(frozen=True)
class SudokuFigureColor:
    text_color: Optional[str]
    background_color: Optional[str]

class SudokuFigureFactory:
    def __init__(self, color: str) -> None:
        self.__color: str = color

    def get_naked_singles_sudoku_figures(self, sudoku: Sudoku) -> List[Figure]:
        n, n_isqrt = sudoku.shape()
        figures: List[Figure] = []
        for candidate in sudoku.candidates_0th_layer_naked_singles:
            i, j = candidate.position
            color_positions: Set[Tuple[int, int]] = {
                *[(ii, j) for ii in range(n)],
                *[(i, jj) for jj in range(n)]
            }

            i0, j0 = (i // n_isqrt) * n_isqrt, (j // n_isqrt) * n_isqrt
            color_positions.update(
                (i0 + a, j0 + b)
                for a in range(n_isqrt)
                for b in range(n_isqrt)
            )

            fig, (ax_start, ax_end) = self.__subplots(n, narrows=2)
            self.__plot_sudoku_on_axis(
                ax=ax_start,
                sudoku=sudoku,
                color_positions={
                    SudokuFigureColor(text_color=None, background_color=self.__color): list(color_positions)
                },
                candidate_positions={
                    SudokuCandidateType.ZEROTH_LAYER_NAKED_SINGLES: [
                        candidate.position
                    ]
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
            color_positions={
                SudokuFigureColor(text_color=self.__color, background_color=None): [
                    sudoku_candidate.position
                ]
            },
            circle_positions=[
                sudoku_candidate.position
            ]
        )

    def __plot_sudoku_on_axis(
            self,
            ax: Axes,
            sudoku: Sudoku,
            color_positions: Optional[Dict[SudokuFigureColor, List[Tuple[int, int]]]] = None,
            candidate_positions: Optional[Dict[SudokuCandidateType, List[Tuple[int, int]]]] = None,
            circle_positions: Optional[List[Tuple[int, int]]] = None,
            arrow_positions: Optional[List[Tuple[Tuple[int, int], Tuple[int, int]]]] = None
    ) -> None:
        n, n_isqrt = sudoku.shape()
        ax.set_xlim(0, n)
        ax.set_ylim(0, n)
        ax.set_aspect("equal")
        ax.axis("off")

        # Draw the base grid and its numbers
        text_positions: Dict[Tuple[int, int], Text] = {}
        for i, j in itertools.product(range(n), range(n)):
            ax.add_patch(Rectangle(self.__cell_bottom_left(n, i, j), width=1, height=1, fill=False, linewidth=0.75))
            if sudoku.grid[i][j] != 0:
                text_positions[(i, j)] = ax.text(*self.__cell_center(n, i, j), s=str(sudoku.grid[i][j]), va="center", ha="center", fontsize=18)

        # Apply text and background colors
        for color_config, positions in (color_positions or {}).items():
            for (i, j) in positions:
                if color_config.background_color is not None:
                    ax.add_patch(
                        Rectangle(
                            self.__cell_bottom_left(n, i, j),
                            width=1,
                            height=1,
                            alpha=0.35,
                            edgecolor="none",
                            facecolor=color_config.background_color
                        )
                    )

                if color_config.text_color and (i, j) in text_positions:
                    text_positions[(i, j)].set_color(color_config.text_color)

        # Draw candidate values inside empty cells
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
                ax.text(*self.__cell_top_left(n, i, j, margins=(+0.05, -0.05)), s=text, ha="left", va="top", fontsize=12, color=self.__color)

        # Draw circles between cells
        for (i, j) in circle_positions or []:
            ax.add_patch(
                Circle(
                    self.__cell_center(n, i, j),
                    radius=0.35,
                    linewidth=1.5,
                    fill=False,
                    edgecolor=self.__color
                )
            )

        # Draw arrows between cells
        for ((i0, j0), (i1, j1)) in arrow_positions or []:
            ax.add_patch(
                FancyArrowPatch(
                    self.__cell_center(n, i0, j0),
                    self.__cell_center(n, i1, j1),
                    arrowstyle="simple",
                    mutation_scale=15,
                    linewidth=0.25,
                    color=self.__color
                )
            )

        # Draw inner and outer borders
        for i in range(0, n + 1, n_isqrt):
            ax.plot((0, n), (i, i), linewidth=1.5, color="black")
            ax.plot((i, i), (0, n), linewidth=1.5, color="black")
        ax.add_patch(Rectangle((0, 0), width=n, height=n, fill=False, linewidth=3))

    @classmethod
    def __subplots(cls, n: int, narrows: int) -> Tuple[Figure, Tuple[Axes, Axes, ...]]:
        size: int = math.floor(n * 0.75)
        return plt.subplots(narrows, 1, figsize=(size, size * narrows))

    @classmethod
    def __cell_bottom_left(cls, n: int, i: int, j: int, margins: Optional[Tuple[float, float]] = None) -> Tuple[float, float]:
        mx, my = margins or (0, 0)
        return j + mx, n - i - 1 + my

    @classmethod
    def __cell_top_left(cls, n: int, i: int, j: int, margins: Optional[Tuple[float, float]] = None) -> Tuple[float, float]:
        mx, my = margins or (0, 0)
        return j + mx, n - i + my

    @classmethod
    def __cell_center(cls, n: int, i: int, j: int, margins: Optional[Tuple[float, float]] = None) -> Tuple[float, float]:
        mx, my = margins or (0, 0)
        return j + 0.5 + mx, n - i - 0.5 + my

if __name__ == "__main__":
    sf = SudokuFigureFactory(color="red")
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
