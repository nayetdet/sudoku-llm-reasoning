import itertools
import math
import matplotlib
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Set
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch
from matplotlib.text import Text
from core.enums.sudoku_candidate_type import SudokuCandidateType
from core.sudoku import Sudoku, SudokuCandidate, SudokuConsensusDeductionChain

matplotlib.use("Agg")

@dataclass(frozen=True)
class SudokuFigureElementOverlay[T]:
    element: T
    color: Optional[str] = None

@dataclass(frozen=True)
class SudokuFigureCircleCandidateElementOverlay:
    value: int
    excluded_positions: Optional[List[Tuple[int, int]]]

@dataclass(frozen=True)
class SudokuFigureOverlay:
    text_color_cells: List[SudokuFigureElementOverlay[Tuple[int, int]]] = field(default_factory=list)
    candidate_cells: Dict[SudokuCandidateType, List[SudokuFigureElementOverlay[Tuple[int, int]]]] = field(default_factory=dict)
    circle_candidate_values: List[SudokuFigureCircleCandidateElementOverlay] = field(default_factory=list)
    circle_cells: List[SudokuFigureElementOverlay[Tuple[int, int]]] = field(default_factory=list)
    arrow_cells: List[SudokuFigureElementOverlay[Tuple[Tuple[int, int], Tuple[int, int]]]] = field(default_factory=list)

class SudokuFigureFactory:
    def __init__(self, primary_color: str, secondary_color: str, tertiary_color: str) -> None:
        self.__primary_color: str = primary_color
        self.__secondary_color: str = secondary_color
        self.__tertiary_color: str = tertiary_color

    def get_naked_singles_sudoku_figures(self, sudoku: Sudoku) -> List[Figure]:
        return self.__get_single_candidate_principle_sudoku_figures(sudoku, sudoku.candidates_0th_layer_naked_singles)

    def get_hidden_singles_sudoku_figures(self, sudoku: Sudoku) -> List[Figure]:
        return self.__get_single_candidate_principle_sudoku_figures(sudoku, sudoku.candidates_0th_layer_hidden_singles)

    def get_consensus_sudoku_figures(self, sudoku: Sudoku) -> List[Figure]:
        n: int = len(sudoku)
        figures: List[Figure] = []
        for candidate in sudoku.candidates_1st_layer_consensus:
            deduction_chains: List[List[SudokuConsensusDeductionChain]] = sudoku.deduction_chain_1st_layer_consensus_at_position(*candidate.position)
            for deduction_chain in deduction_chains:
                width: int = max(1, len(deduction_chain)) | 1
                width_middle: int = width // 2

                fig, ax = self.__subplots(n, width=width, height=3)
                initial_sub_ax: Axes = self.__sub_ax(ax, position=(0, width_middle))
                self.__plot_sudoku_on_sub_ax(
                    sub_ax=initial_sub_ax,
                    sudoku=sudoku,
                    overlay=SudokuFigureOverlay(
                        candidate_cells={
                            SudokuCandidateType.ZEROTH_LAYER: [
                                SudokuFigureElementOverlay(element=element, color=self.__primary_color if element == candidate.position else self.__tertiary_color)
                                for element in {position for x in deduction_chain for position in x.region_positions} | {candidate.position}
                            ]
                        },
                        circle_candidate_values=[
                            SudokuFigureCircleCandidateElementOverlay(value=deduction_chain[0].initial_assumption_value, excluded_positions=[candidate.position])
                        ]
                    )
                )

                current_sudoku: Sudoku = sudoku
                middle_sub_axes: List[Axes] = []
                for step_column, deduction in enumerate(deduction_chain):
                    if len(deduction_chain) % 2 == 0 and step_column >= width_middle:
                        step_column += 1

                    current_sudoku = current_sudoku.next_step_at_position(
                        deduction.initial_assumption_position[0],
                        deduction.initial_assumption_position[1],
                        deduction.initial_assumption_value
                    )

                    for consequence in deduction.consequences:
                        current_sudoku = current_sudoku.next_step_at_position(
                            consequence[0][0],
                            consequence[0][1],
                            consequence[1]
                        )

                    middle_sub_ax: Axes = self.__sub_ax(ax, position=(1, step_column))
                    middle_consequence_positions: List[Tuple[int, int]] = [consequence[0] for consequence in deduction.consequences]
                    self.__plot_sudoku_on_sub_ax(
                        sub_ax=middle_sub_ax,
                        sudoku=current_sudoku,
                        overlay=SudokuFigureOverlay(
                            text_color_cells=[
                                SudokuFigureElementOverlay(element=x, color=self.__primary_color if x == candidate.position else self.__secondary_color if x == deduction.initial_assumption_position else self.__tertiary_color)
                                for x in middle_consequence_positions
                            ],
                            circle_cells=[
                                SudokuFigureElementOverlay(element=candidate.position, color=self.__primary_color),
                                SudokuFigureElementOverlay(element=deduction.initial_assumption_position, color=self.__secondary_color)
                            ],
                            arrow_cells=[
                                SudokuFigureElementOverlay(element=x, color=self.__primary_color)
                                for x in [
                                    (middle_consequence_positions[i], middle_consequence_positions[i + 1])
                                    for i in range(len(middle_consequence_positions) - 1)
                                ]
                            ]
                        )
                    )

                    middle_sub_axes.append(middle_sub_ax)
                final_sub_ax: Axes = self.__sub_ax(ax, position=(2, width_middle))
                self.__plot_final_sudoku_on_sub_ax(sub_ax=final_sub_ax, sudoku=sudoku, candidate=candidate)
                self.__connect_ax(ax, initial_sub_ax, final_sub_ax, middle_sub_axes=middle_sub_axes)
                figures.append(fig)
        return figures

    def __get_single_candidate_principle_sudoku_figures(self, sudoku: Sudoku, candidates: Tuple[SudokuCandidate, ...]) -> List[Figure]:
        n: int = len(sudoku)
        figures: List[Figure] = []
        for candidate in candidates:
            fig, ax = self.__subplots(n, width=1, height=2)
            initial_sub_ax, final_sub_ax = self.__sub_ax(ax, position=(0, 0)), self.__sub_ax(ax, position=(1, 0))
            self.__plot_sudoku_on_sub_ax(
                sub_ax=initial_sub_ax,
                sudoku=sudoku,
                overlay=SudokuFigureOverlay(
                    candidate_cells={
                        SudokuCandidateType.ZEROTH_LAYER_PLAIN: [
                            SudokuFigureElementOverlay(element=candidate.position, color=self.__primary_color)
                        ]
                    }
                )
            )

            self.__plot_final_sudoku_on_sub_ax(final_sub_ax, sudoku=sudoku, candidate=candidate)
            self.__connect_ax(ax, initial_sub_ax, final_sub_ax)
            figures.append(fig)
            break
        return figures

    def __plot_final_sudoku_on_sub_ax(self, sub_ax: Axes, sudoku: Sudoku, candidate: SudokuCandidate) -> None:
        return self.__plot_sudoku_on_sub_ax(
            sub_ax=sub_ax,
            sudoku=sudoku.next_step_at_position(*candidate.position, candidate.value),
            overlay=SudokuFigureOverlay(
                text_color_cells=[
                    SudokuFigureElementOverlay(element=candidate.position, color=self.__primary_color)
                ],
                circle_cells=[
                    SudokuFigureElementOverlay(element=candidate.position, color=self.__primary_color)
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
            sub_ax.add_patch(
                Rectangle(
                    self.__cell_bottom_left(n, position=(i, j)),
                    width=1,
                    height=1,
                    fill=False,
                    linewidth=0.75,
                    zorder=3
                )
            )

            if sudoku.grid[i][j] != 0:
                text_positions[(i, j)] = sub_ax.text(
                    *self.__cell_center(n, position=(i, j)),
                    s=str(sudoku.grid[i][j]),
                    ha="center",
                    va="center",
                    fontsize=20
                )

        # Text Colors
        for cell in overlay.text_color_cells:
            position: Tuple[int, int] = cell.element
            if position in text_positions:
                text_positions[position].set_color(cell.color or "black")

        # Candidates
        n_inv_isqrt: float = 1 / n_isqrt
        for candidate_type, cells in overlay.candidate_cells.items():
            for cell in cells:
                i, j = cell.element
                if sudoku.grid[i][j] != 0:
                    continue

                candidates: Optional[Set[int]] = sudoku.candidate_values_at_position(i, j, candidate_type=candidate_type)
                if not candidates:
                    continue

                color: str = cell.color or self.__primary_color
                x0, y0 = self.__cell_top_left(n, position=(i, j), margins=(0, -0.05) if n > 4 else None)
                for idx, candidate in enumerate(sorted(candidates)):
                    row, column = divmod(idx, n_isqrt)
                    x, y = x0 + n_inv_isqrt * (column + 0.5), y0 - n_inv_isqrt * (row + 0.5)
                    highlighted: bool = any(
                        candidate == circle_candidate.value and (circle_candidate.excluded_positions is None or (i, j) not in circle_candidate.excluded_positions)
                        for circle_candidate in overlay.circle_candidate_values or []
                    )

                    sub_ax.text(
                        x=x,
                        y=y,
                        s=str(candidate),
                        ha="center",
                        va="center",
                        fontsize=12 if n > 4 else 15,
                        color=color if not highlighted else self.__secondary_color
                    )

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
                self.__cell_bottom_right(n, position=position, margins=(-0.25, +0.16))
                for position in [overlay.arrow_cells[0].element[0], *[cell.element[1] for cell in overlay.arrow_cells]]
            ]

            sub_ax.plot(*zip(*positions), linewidth=1.5, alpha=0.5, linestyle="-", zorder=1, color=color)
            for idx, position in enumerate(positions):
                sub_ax.text(
                    *position,
                    s=f"{idx:02d}",
                    ha="center",
                    va="center",
                    weight="bold",
                    fontsize=10,
                    path_effects=[
                        pe.Stroke(linewidth=3, foreground="white"),
                        pe.Normal()
                    ],
                    zorder=2,
                    color=color
                )

        # Borders
        for i in range(0, n + 1, n_isqrt):
            sub_ax.plot((0, n), (i, i), linewidth=1.5, color="black")
            sub_ax.plot((i, i), (0, n), linewidth=1.5, color="black")
        sub_ax.add_patch(Rectangle((0, 0), n, n, fill=False, linewidth=3, zorder=3))

    @classmethod
    def __subplots(cls, n: int, width: int, height: int) -> Tuple[Figure, Axes]:
        size: int = math.floor(n * 0.75)
        fig, ax = plt.subplots(figsize=(width * size, height * size))
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

        fig.tight_layout(pad=0)
        fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        return fig, ax

    @classmethod
    def __sub_ax(cls, ax: Axes, position: Tuple[int, int], margins: Optional[Tuple[float, float]] = None) -> Axes:
        (row, column), (dx, dy) = position, margins or (0, 0.2)
        width, height = 1 - dx, 1 - dy
        x0, y0 = column + dx / 2, row + dy / 2
        sub_ax: Axes = ax.inset_axes((x0, y0, width, height), transform=ax.transData)
        sub_ax.set_box_aspect(1)
        return sub_ax

    @classmethod
    def __connect_ax(cls, ax: Axes, initial_sub_ax: Axes, final_sub_ax: Axes, middle_sub_axes: Optional[List[Axes]] = None) -> None:
        def add_arrow(sub_ax_from: Axes, sub_ax_to: Axes):
            ax.add_patch(
                FancyArrowPatch(
                    posA=ax.transData.inverted().transform(sub_ax_from.transAxes.transform((0.5, 0))).tolist(),
                    posB=ax.transData.inverted().transform(sub_ax_to.transAxes.transform((0.5, 1))).tolist(),
                    arrowstyle="-|>",
                    mutation_scale=10,
                    linewidth=3,
                    color="black",
                    clip_on=False
                )
            )

        if middle_sub_axes is not None:
            for middle_sub_ax in middle_sub_axes:
                add_arrow(initial_sub_ax, middle_sub_ax)
                add_arrow(middle_sub_ax, final_sub_ax)
        else: add_arrow(initial_sub_ax, final_sub_ax)

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
