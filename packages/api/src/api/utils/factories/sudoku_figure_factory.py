import itertools
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
class SudokuFigureColor:
    text_color: Optional[str]
    background_color: Optional[str]

@dataclass(frozen=True)
class SudokuFigureOverlay:
    color_positions: Dict["SudokuFigureColor", List[Tuple[int, int]]] = field(default_factory=dict)
    candidate_positions: Dict[SudokuCandidateType, List[Tuple[int, int]]] = field(default_factory=dict)
    circle_positions: List[Tuple[int, int]] = field(default_factory=list)
    arrow_positions: List[Tuple[Tuple[int, int], Tuple[int, int]]] = field(default_factory=list)

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

            fig, ax = self.__subplots(width=1, height=3)
            initial_sub_ax, final_sub_ax = self.__sub_ax(ax, position=(0, 0)), self.__sub_ax(ax, position=(2, 0))
            self.__plot_sudoku_on_sub_ax(
                sub_ax=initial_sub_ax,
                sudoku=sudoku,
                overlay=SudokuFigureOverlay(
                    color_positions={
                        SudokuFigureColor(text_color=self.__color, background_color=None): [
                            candidate.position
                        ]
                    },
                    candidate_positions={
                        SudokuCandidateType.ZEROTH_LAYER_NAKED_SINGLES: [
                            candidate.position
                        ]
                    }
                )
            )

            self.__plot_final_sudoku_on_sub_ax(final_sub_ax, sudoku=sudoku, sudoku_candidate=candidate)
            figures.append(fig)
        return figures

    def get_hidden_singles_sudoku_figures(self, sudoku: Sudoku) -> List[Figure]:
        figures: List[Figure] = []
        for candidate in sudoku.candidates_0th_layer_hidden_singles:
            fig, ax = self.__subplots(width=1, height=3)
            initial_sub_ax, final_sub_ax = self.__sub_ax(ax, position=(0, 0)), self.__sub_ax(ax, position=(2, 0))
            self.__plot_sudoku_on_sub_ax(
                sub_ax=initial_sub_ax,
                sudoku=sudoku,
                overlay=SudokuFigureOverlay(
                    candidate_positions={
                        SudokuCandidateType.ZEROTH_LAYER_PLAIN: [
                            candidate.position
                        ]
                    }
                )
            )

            self.__plot_final_sudoku_on_sub_ax(final_sub_ax, sudoku=sudoku, sudoku_candidate=candidate)
            self.__conect_axs(ax)
            figures.append(fig)

        return figures

    def get_consensus_sudoku_figures(self, sudoku: Sudoku) -> List[Figure]:
        n, n_isqrt = sudoku.shape()
        figures: List[Figure] = []
        for candidate in sudoku.candidates_1st_layer_consensus:
            i, j = candidate.position
            deduction_chains: List[List[SudokuConsensusDeductionChain]] = sudoku.deduction_chain_1st_layer_consensus(i, j)
            for chain in deduction_chains:
                
                height: int = 5
                width_size = len(chain) if len(chain) % 2 == 1 else len(chain) + 1
                middle_index: int = width_size // 2
                fig, ax = self.__subplots(width=width_size, height=height)
                initial_sub_ax = self.__sub_ax(ax, position=(0, middle_index))
                final_sub_ax = self.__sub_ax(ax, position=(height - 1, middle_index))

                # Plot initial sudoku
                self.__plot_sudoku_on_sub_ax(
                    sub_ax=initial_sub_ax,
                    sudoku=sudoku,
                    overlay=SudokuFigureOverlay(
                        color_positions={
                            SudokuFigureColor(text_color=self.__color, background_color="red"): [
                                candidate.position
                            ]
                        },
                        candidate_positions={
                            SudokuCandidateType.FIRST_LAYER_CONSENSUS: [
                                candidate.position
                            ]
                        }
                    )
                )

            # Plot middle sudoku
                current_sudoku: Sudoku = sudoku
                consequences_arrows: List[Tuple[Tuple[int, int], Tuple[int, int]]] = []
                for step_index, deduction in enumerate(chain):
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
                    consequences_positions = [consequence[0] for consequence in deduction.consequences]
                    for i in range(0, len(consequences_positions), 2):
                        if i + 1 < len(consequences_positions):
                            consequences_arrows.append((consequences_positions[i], consequences_positions[i+1]))
                    
                    step_sub_ax = self.__sub_ax(ax, position=(height // 2, step_index))
                    arrow_initial_position = deduction.initial_assumption_position
                    arrow_final_position = deduction.consequences[0][0]
                    consequences_arrows.append((arrow_initial_position, arrow_final_position))
                    self.__plot_sudoku_on_sub_ax(
                        sub_ax=step_sub_ax,
                        sudoku=current_sudoku,
                        overlay=SudokuFigureOverlay(
                            color_positions={
                                SudokuFigureColor(text_color="orange", background_color=None): [
                                    *consequences_positions
                                ],
                                SudokuFigureColor(text_color=self.__color, background_color="red"): [
                                    deduction.initial_assumption_position
                                ]
                            },
                            arrow_positions=consequences_arrows,
                            circle_positions=[deduction.initial_assumption_position]
                        ),
                    )
                    
                self.__plot_final_sudoku_on_sub_ax(sub_ax=final_sub_ax, sudoku=sudoku, sudoku_candidate=candidate)
                self.__conect_axs(ax)
                figures.append(fig)
                break
        return figures

    def __plot_final_sudoku_on_sub_ax(self, sub_ax: Axes, sudoku: Sudoku, sudoku_candidate: SudokuCandidate) -> None:
        return self.__plot_sudoku_on_sub_ax(
            sub_ax=sub_ax,
            sudoku=sudoku.next_step_at_position(*sudoku_candidate.position, sudoku_candidate.value),
            overlay=SudokuFigureOverlay(
                color_positions={
                    SudokuFigureColor(text_color=self.__color, background_color=None): [
                        sudoku_candidate.position
                    ]
                },
                circle_positions=[
                    sudoku_candidate.position
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

        # Draw the base grid and its numbers
        text_positions: Dict[Tuple[int, int], Text] = {}
        for i, j in itertools.product(range(n), range(n)):
            sub_ax.add_patch(Rectangle(self.__cell_bottom_left(n, position=(i, j)), width=1, height=1, fill=False, linewidth=0.75))
            if sudoku.grid[i][j] != 0:
                text_positions[(i, j)] = sub_ax.text(*self.__cell_center(n, position=(i, j)), s=str(sudoku.grid[i][j]), ha="center", va="center", fontsize=18)

        # Apply text and background colors
        for color_config, positions in overlay.color_positions.items():
            for position in positions:
                if color_config.background_color is not None:
                    sub_ax.add_patch(
                        Rectangle(
                            self.__cell_bottom_left(n, position=position),
                            width=1,
                            height=1,
                            alpha=0.35,
                            edgecolor="none",
                            facecolor=color_config.background_color
                        )
                    )

                if color_config.text_color and position in text_positions:
                    text_positions[position].set_color(color_config.text_color)

        # Draw candidate values inside empty cells
        for candidate_type, positions in overlay.candidate_positions.items():
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
                sub_ax.text(*self.__cell_top_left(n, position=(i, j), margins=(+0.05, -0.05)), s=text, ha="left", va="top", fontsize=12, color=self.__color)

        # Draw circles between cells
        for position in overlay.circle_positions:
            sub_ax.add_patch(
                Circle(
                    self.__cell_center(n, position=position),
                    radius=0.35,
                    linewidth=1.5,
                    fill=False,
                    edgecolor=self.__color
                )
            )

        # Draw arrows between cells
        for (initial_position, final_position) in overlay.arrow_positions:
            sub_ax.add_patch(
                FancyArrowPatch(
                    self.__cell_center(n, position=initial_position),
                    self.__cell_center(n, position=final_position),
                    arrowstyle="simple",
                    mutation_scale=15,
                    linewidth=0.25,
                    color=self.__color
                )
            )

        # Draw inner and outer borders
        for i in range(0, n + 1, n_isqrt):
            sub_ax.plot((0, n), (i, i), linewidth=1.5, color="black")
            sub_ax.plot((i, i), (0, n), linewidth=1.5, color="black")
        sub_ax.add_patch(Rectangle((0, 0), width=n, height=n, fill=False, linewidth=3))

    @classmethod
    def __subplots(cls, width: int, height: int) -> Tuple[Figure, Axes]:
        fig, ax = plt.subplots()
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
    def __conect_axs(cls, external_ax: Axes) -> None:
        sub_entries = getattr(external_ax, "_sudoku_sub_axes", None)
        if not sub_entries:
            return

        x0, x1 = external_ax.get_xlim()
        y0, y1 = external_ax.get_ylim()
        width  = int(round(max(x0, x1)))
        height = int(round(max(y0, y1)))

        mid_col = width // 2
        mid_row = height // 2

        pos_to_ax = {pos: sa for (sa, pos) in sub_entries}
        initial_pos = (0, mid_col)
        final_pos   = (height - 1, mid_col)

        step_positions = sorted(
            [pos for pos in pos_to_ax.keys()
            if pos[0] == mid_row and pos not in (initial_pos, final_pos)],
            key=lambda p: p[1]
        )


        def add_arrow(p0: Tuple[int, int], p1: Tuple[int, int], rad: float = 0.0) -> None:
            external_ax.add_patch(
                FancyArrowPatch(
                    (p0[1] + 0.5, p0[0] + 1),
                    (p1[1] + 0.5, p1[0]),
                    arrowstyle="simple",
                    mutation_scale=15,
                    linewidth=0.75,
                    color="black",
                    connectionstyle=f"arc3,rad={rad}"
                )
            )

        has_initial = initial_pos in pos_to_ax
        has_final   = final_pos in pos_to_ax

        # not consensus
        if not step_positions:
            if has_initial and has_final:
                add_arrow(initial_pos, final_pos, rad=0.0)
            return

        # consensus
        for step in step_positions:
            dist = step[1] - mid_col
            base = 0.15  
            rad_out = base * (1 if dist >= 0 else -1) * (abs(dist) / max(1, mid_col))
            rad_in  = -rad_out * 0.9

            if has_initial:
                add_arrow(initial_pos, step, rad=rad_out)
            if has_final:
                add_arrow(step, final_pos, rad=rad_in)

    @classmethod
    def __sub_ax(cls, ax: Axes, position: Tuple[int, int]) -> Axes:
        sub_ax = ax.inset_axes((position[1], position[0], 1, 1), transform=ax.transData)
        setattr(sub_ax, "_sudoku_pos", position)
        if not hasattr(ax, "_sudoku_sub_axes"):
            ax._sudoku_sub_axes = []  # type: ignore[attr-defined]
        ax._sudoku_sub_axes.append((sub_ax, position))  # type: ignore[attr-defined]
        return sub_ax

    @classmethod
    def __cell_bottom_left(cls, n: int, position: Tuple[int, int], margins: Optional[Tuple[float, float]] = None) -> Tuple[float, float]:
        (i, j), (dx, dy) = position, margins or (0, 0)
        return j + dx, n - i - 1 + dy

    @classmethod
    def __cell_top_left(cls, n: int, position: Tuple[int, int], margins: Optional[Tuple[float, float]] = None) -> Tuple[float, float]:
        (i, j), (dx, dy) = position, margins or (0, 0)
        return j + dx, n - i + dy

    @classmethod
    def __cell_center(cls, n: int, position: Tuple[int, int], margins: Optional[Tuple[float, float]] = None) -> Tuple[float, float]:
        (i, j), (dx, dy) = position, margins or (0, 0)
        return j + 0.5 + dx, n - i - 0.5 + dy

if __name__ == "__main__":
    sf = SudokuFigureFactory(color="red")
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
