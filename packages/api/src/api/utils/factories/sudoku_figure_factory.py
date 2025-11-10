import itertools
import math
import matplotlib.pyplot as plt
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Set
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle, FancyArrowPatch, Circle
from matplotlib.text import Text
from core.enums.sudoku_candidate_type import SudokuCandidateType
from core.sudoku import Sudoku, SudokuCandidate, SudokuConsensusDeductionChain

@dataclass(frozen=True)
class SudokuFigureCellOverlay[T]:
    element: T
    color: Optional[str] = None

@dataclass(frozen=True)
class SudokuFigureOverlay:
    text_color_cells: List[SudokuFigureCellOverlay[Tuple[int, int]]] = field(default_factory=list)
    candidate_cells: Dict[SudokuCandidateType, List[SudokuFigureCellOverlay[Tuple[int, int]]]] = field(default_factory=dict)
    circle_cells: List[SudokuFigureCellOverlay[Tuple[int, int]]] = field(default_factory=list)
    arrow_cells: List[SudokuFigureCellOverlay[Tuple[Tuple[int, int], Tuple[int, int]]]] = field(default_factory=list)

class SudokuFigureFactory:
    def __init__(self, primary_color: str, secondary_color: str) -> None:
        self.__primary_color: str = primary_color
        self.__secondary_color: str = secondary_color

    def get_naked_singles_sudoku_figures(self, sudoku: Sudoku) -> List[Figure]:
        n: int = len(sudoku)
        figures: List[Figure] = []
        for candidate in sudoku.candidates_0th_layer_naked_singles:
            fig, ax = self.__subplots(n, width=1, height=2)
            initial_sub_ax, final_sub_ax = self.__sub_ax(ax, position=(0, 0)), self.__sub_ax(ax, position=(1, 0))
            self.__plot_sudoku_on_sub_ax(
                sub_ax=initial_sub_ax,
                sudoku=sudoku,
                overlay=SudokuFigureOverlay(
                    candidate_cells={
                        SudokuCandidateType.ZEROTH_LAYER_PLAIN: [
                            SudokuFigureCellOverlay(element=candidate.position, color=self.__primary_color)
                        ]
                    }
                )
            )

            self.__plot_final_sudoku_on_sub_ax(final_sub_ax, sudoku=sudoku, sudoku_candidate=candidate)
            figures.append(fig)
        return figures

    def get_hidden_singles_sudoku_figures(self, sudoku: Sudoku) -> List[Figure]:
        n: int = len(sudoku)
        figures: List[Figure] = []
        for candidate in sudoku.candidates_0th_layer_hidden_singles:
            fig, ax = self.__subplots(n, width=1, height=2)
            initial_sub_ax, final_sub_ax = self.__sub_ax(ax, position=(0, 0)), self.__sub_ax(ax, position=(1, 0))
            self.__plot_sudoku_on_sub_ax(
                sub_ax=initial_sub_ax,
                sudoku=sudoku,
                overlay=SudokuFigureOverlay(
                    candidate_cells={
                        SudokuCandidateType.ZEROTH_LAYER_PLAIN: [
                            SudokuFigureCellOverlay(element=candidate.position, color=self.__primary_color)
                        ]
                    }
                )
            )

            self.__plot_final_sudoku_on_sub_ax(final_sub_ax, sudoku=sudoku, sudoku_candidate=candidate)
            figures.append(fig)
        return figures

    def get_consensus_sudoku_figures(self, sudoku: Sudoku) -> List[Figure]:
        n: int = len(sudoku)
        figures: List[Figure] = []
        for candidate in sudoku.candidates_1st_layer_consensus:
            deduction_chains: List[List[SudokuConsensusDeductionChain]] = sudoku.deduction_chain_1st_layer_consensus(*candidate.position)
            for deduction_chain in deduction_chains:
                width: int = math.isqrt(len(deduction_chain)) | 1
                height: int = width + 2

                fig, ax = self.__subplots(n, width=width, height=height)
                initial_sub_ax: Axes = self.__sub_ax(ax, position=(0, width // 2))
                self.__plot_sudoku_on_sub_ax(
                    sub_ax=initial_sub_ax,
                    sudoku=sudoku,
                    overlay=SudokuFigureOverlay(
                        candidate_cells={
                            SudokuCandidateType.ZEROTH_LAYER: [
                                SudokuFigureCellOverlay(element=element, color=self.__primary_color if element == candidate.position else self.__secondary_color)
                                for element in {position for x in deduction_chain for position in x.region_positions} | {candidate.position}
                            ]
                        }
                    )
                )

                current_sudoku: Sudoku = sudoku
                for step_idx, deduction in enumerate(deduction_chain):
                    current_sudoku = current_sudoku.next_step_at_position(
                        deduction.initial_assumption_position[0],
                        deduction.initial_assumption_position[1],
                        deduction.initial_assumption_value
                    )

                    for consequence in list(deduction.consequences) + [(deduction.consensus_candidate_position, deduction.consensus_candidate_value)]:
                        current_sudoku = current_sudoku.next_step_at_position(
                            consequence[0][0],
                            consequence[0][1],
                            consequence[1]
                        )

                    middle_sub_ax: Axes = self.__sub_ax(ax, position=(1, step_idx - 1))
                    middle_consequence_positions: List[Tuple[int, int]] = [deduction.initial_assumption_position] + [consequence[0] for consequence in deduction.consequences] + [candidate.position]
                    self.__plot_sudoku_on_sub_ax(
                        sub_ax=middle_sub_ax,
                        sudoku=current_sudoku,
                        overlay=SudokuFigureOverlay(
                            text_color_cells=[
                                SudokuFigureCellOverlay(element=x, color=self.__secondary_color)
                                for x in middle_consequence_positions
                            ],
                            circle_cells=[
                                SudokuFigureCellOverlay(element=deduction.initial_assumption_position, color=self.__secondary_color),
                                SudokuFigureCellOverlay(element=candidate.position, color=self.__secondary_color)
                            ],
                            arrow_cells=[
                                SudokuFigureCellOverlay(element=x, color=self.__primary_color)
                                for x in [
                                    (middle_consequence_positions[i], middle_consequence_positions[i + 1])
                                    for i in range(len(middle_consequence_positions) - 1)
                                ]
                            ]
                        )
                    )

                final_sub_ax: Axes = self.__sub_ax(ax, position=(height - 1, width // 2))
                self.__plot_final_sudoku_on_sub_ax(sub_ax=final_sub_ax, sudoku=sudoku, sudoku_candidate=candidate)
                figures.append(fig)
        return figures

    def __plot_final_sudoku_on_sub_ax(self, sub_ax: Axes, sudoku: Sudoku, sudoku_candidate: SudokuCandidate) -> None:
        return self.__plot_sudoku_on_sub_ax(
            sub_ax=sub_ax,
            sudoku=sudoku.next_step_at_position(*sudoku_candidate.position, sudoku_candidate.value),
            overlay=SudokuFigureOverlay(
                text_color_cells=[
                    SudokuFigureCellOverlay(element=sudoku_candidate.position, color=self.__primary_color)
                ],
                circle_cells=[
                    SudokuFigureCellOverlay(element=sudoku_candidate.position, color=self.__primary_color)
                ]
            )
        )

    def __plot_sudoku_on_sub_ax(self, sub_ax: Axes, sudoku: Sudoku, overlay: SudokuFigureOverlay) -> None:
        n, n_isqrt = sudoku.shape()
        sub_ax.set_xlim(0, n)
        sub_ax.set_ylim(0, n)
        sub_ax.set_xticks(np.arange(0, n + 1))
        sub_ax.set_yticks(np.arange(0, n + 1))
        sub_ax.set_xticklabels([])
        sub_ax.set_yticklabels([])
        sub_ax.set_aspect("equal")
        sub_ax.axis("off")

        # Base Grid
        text_positions: Dict[Tuple[int, int], Text] = {}
        for i, j in itertools.product(range(n), range(n)):
            sub_ax.add_patch(Rectangle(self.__cell_bottom_left(n, position=(i, j)), width=1, height=1, fill=False, linewidth=0.75))
            if sudoku.grid[i][j] != 0:
                text_positions[(i, j)] = sub_ax.text(*self.__cell_center(n, position=(i, j)), s=str(sudoku.grid[i][j]), ha="center", va="center", fontsize=18)

        # Text Colors
        for cell in overlay.text_color_cells:
            position: Tuple[int, int] = cell.element
            if position in text_positions:
                text_positions[position].set_color(cell.color or "black")

        # Candidates
        for candidate_type, cells in overlay.candidate_cells.items():
            for cell in cells:
                i, j = cell.element
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
                sub_ax.text(*self.__cell_top_left(n, position=(i, j), margins=(+0.05, -0.05)), s=text, ha="left", va="top", fontsize=12, color=cell.color or self.__primary_color)

        # Circles
        for cell in overlay.circle_cells:
            sub_ax.add_patch(
                Circle(
                    self.__cell_center(n, position=cell.element),
                    radius=0.35,
                    fill=False,
                    edgecolor=cell.color or self.__primary_color,
                    linewidth=1.5
                )
            )

        # Arrows
        if overlay.arrow_cells:
            color: str = overlay.arrow_cells[0].color or self.__primary_color
            positions: List[Tuple[float, float]] = [
                self.__cell_bottom_right(n, position=position, margins=(-0.18, +0.18))
                for position in [overlay.arrow_cells[0].element[0], *[cell.element[1] for cell in overlay.arrow_cells]]
            ]

            sub_ax.plot(*zip(*positions), color=color, linewidth=1.5, alpha=0.45, linestyle="-", zorder=1)
            for idx, position in enumerate(positions):
                sub_ax.text(*position, s=str(idx) if idx not in (0, len(positions) - 1) else "@", ha="center", va="center", weight="bold", fontsize=8, color=color, zorder=1)

            sub_ax.add_patch(
                FancyArrowPatch(
                    posA=positions[-2],
                    posB=positions[-1],
                    arrowstyle="->",
                    linewidth=1.5,
                    color=color,
                    alpha=0.45,
                    mutation_scale=15,
                    zorder=1
                )
            )

        # Borders
        for i in range(0, n + 1, n_isqrt):
            sub_ax.plot((0, n), (i, i), linewidth=1.5, color="black")
            sub_ax.plot((i, i), (0, n), linewidth=1.5, color="black")
        sub_ax.add_patch(Rectangle((0, 0), n, n, fill=False, linewidth=3))

    @classmethod
    def __subplots(cls, n: int, width: int, height: int) -> Tuple[Figure, Axes]:
        size: float = n * 0.75
        fig, ax = plt.subplots(figsize=(width * size ** 2, height * size))
        ax.set_xlim(0, width)
        ax.set_ylim(0, height)
        ax.set_xticks(np.arange(0, width + 1))
        ax.set_yticks(np.arange(0, height + 1))
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.set_aspect("equal")
        ax.axis("off")
        ax.grid(True)
        ax.invert_yaxis()
        return fig, ax

    @classmethod
    def __sub_ax(cls, ax: Axes, position: Tuple[int, int], margin: float = 0.18) -> Axes:
        size: float = 1 - margin
        row, column = position
        x0, y0 = column + margin / 2, row + margin / 2
        return ax.inset_axes((x0, y0, size, size), transform=ax.transData)

    @classmethod
    def __connect_sub_ax(cls, initial_sub_ax: Axes, final_sub_ax: Axes, middle_sub_axes: Optional[List[Axes]] = None) -> None:
        raise NotImplementedError()

    @classmethod
    def __cell_bottom_left(cls, n: int, position: Tuple[int, int], margins: Optional[Tuple[float, float]] = None) -> Tuple[float, float]:
        (i, j), (dx, dy) = position, margins or (0, 0)
        return j + dx, n - i - 1 + dy

    @classmethod
    def __cell_bottom_right(cls, n: int, position: Tuple[int, int], margins: Optional[Tuple[float, float]] = None) -> Tuple[float, float]:
        (i, j), (dx, dy) = position, margins or (0, 0)
        return j + 1 + dx, n - i - 1 + dy

    @classmethod
    def __cell_top_left(cls, n: int, position: Tuple[int, int], margins: Optional[Tuple[float, float]] = None) -> Tuple[float, float]:
        (i, j), (dx, dy) = position, margins or (0, 0)
        return j + dx, n - i + dy

    @classmethod
    def __cell_center(cls, n: int, position: Tuple[int, int], margins: Optional[Tuple[float, float]] = None) -> Tuple[float, float]:
        (i, j), (dx, dy) = position, margins or (0, 0)
        return j + 0.5 + dx, n - i - 0.5 + dy

if __name__ == "__main__":
    sf = SudokuFigureFactory(primary_color="red", secondary_color="blue")
    sf.get_consensus_sudoku_figures(
        Sudoku(
            grid=[
                [0, 0, 0, 0],
                [0, 4, 2, 0],
                [4, 0, 3, 0],
                [0, 3, 0, 0]
            ]
        )
    )

    plt.show()
