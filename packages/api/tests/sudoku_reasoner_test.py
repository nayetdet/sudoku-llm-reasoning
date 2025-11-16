from dataclasses import dataclass
from typing import Callable, Tuple

import pytest

from api.mappers.sudoku_mapper import SudokuMapper
from api.repositories.reasoner_accuracy_repository import ReasonerAccuracyRepository
from api.repositories.sudoku_repository import SudokuRepository
from core.enums.sudoku_candidate_type import SudokuCandidateType
from core.sudoku import Sudoku, SudokuCandidate
from core.sudoku_reasoner import SudokuReasoner


ACCURACY_SAMPLE_SIZE: int = 100


@dataclass(frozen=True)
class TechniqueScenario:
    label: str
    grid_size: int
    candidate_type: SudokuCandidateType
    solver: Callable[[SudokuReasoner, Sudoku], object]
    verified_attr: str


def _run_accuracy_check(sudoku_reasoner: SudokuReasoner, scenario: TechniqueScenario) -> None:
    successes: int = 0
    failures: list[str] = []

    for attempt in range(ACCURACY_SAMPLE_SIZE):
        sudoku_model = SudokuRepository.get_random(
            n=scenario.grid_size,
            candidate_type=scenario.candidate_type.value,
        )
        if sudoku_model is None:
            pytest.skip(f"Não há Sudokus cadastrados para {scenario.candidate_type}.")

        sudoku: Sudoku = SudokuMapper.to_sudoku(sudoku_model)
        verified_candidates: Tuple[SudokuCandidate, ...] = getattr(sudoku, scenario.verified_attr)

        assert verified_candidates, (
            f"O Sudoku id={getattr(sudoku_model, 'id', 'desconhecido')} "
            f"não possui candidatos para {scenario.label}. Revise o dataset."
        )

        result_schema = scenario.solver(sudoku_reasoner, sudoku)
        llm_response = SudokuMapper.to_sudoku_candidate(result_schema)

        if llm_response in verified_candidates:
            successes += 1
        else:
            failures.append(
                f"#{attempt + 1} id={getattr(sudoku_model, 'id', 'desconhecido')} "
                f"esperado∈{verified_candidates}, obtido={llm_response}"
            )

    accuracy: float = successes / ACCURACY_SAMPLE_SIZE
    print(f"[{scenario.label}] acurácia: {accuracy:.2%} ({successes}/{ACCURACY_SAMPLE_SIZE})")

    ReasonerAccuracyRepository.upsert_result(
        technique=scenario.label,
        sample_size=ACCURACY_SAMPLE_SIZE,
        successes=successes,
    )

    if failures:
        preview = "\n".join(failures[:5])
        print(
            f"[WARN] {scenario.label} falhou em {len(failures)} de {ACCURACY_SAMPLE_SIZE} execuções "
            f"(acurácia {accuracy:.2%}). Exemplos:\n{preview}"
        )


def test_naked_singles_analysis(sudoku_reasoner: SudokuReasoner) -> None:
    _run_accuracy_check(
        sudoku_reasoner,
        TechniqueScenario(
            label="Naked Singles",
            grid_size=9,
            candidate_type=SudokuCandidateType.ZEROTH_LAYER_NAKED_SINGLES,
            solver=SudokuReasoner.solve_naked_singles,
            verified_attr="candidates_0th_layer_naked_singles",
        ),
    )


def test_hidden_singles_analysis(sudoku_reasoner: SudokuReasoner) -> None:
    _run_accuracy_check(
        sudoku_reasoner,
        TechniqueScenario(
            label="Hidden Singles",
            grid_size=9,
            candidate_type=SudokuCandidateType.ZEROTH_LAYER_HIDDEN_SINGLES,
            solver=SudokuReasoner.solve_hidden_singles,
            verified_attr="candidates_0th_layer_hidden_singles",
        ),
    )


def test_consensus_analysis(sudoku_reasoner: SudokuReasoner) -> None:
    _run_accuracy_check(
        sudoku_reasoner,
        TechniqueScenario(
            label="Consensus Principle",
            grid_size=4,
            candidate_type=SudokuCandidateType.FIRST_LAYER_CONSENSUS,
            solver=SudokuReasoner.solve_consensus_principle,
            verified_attr="candidates_1st_layer_consensus",
        ),
    )
