import pytest
from dataclasses import dataclass
from typing import Callable, Tuple
from api.mappers.sudoku_mapper import SudokuMapper
from api.repositories.sudoku_repository import SudokuRepository
from core.enums.sudoku_candidate_type import SudokuCandidateType
from core.sudoku import Sudoku, SudokuCandidate
from core.sudoku_reasoner import SudokuReasoner

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
    sudoku_models = SudokuRepository.get_all(
        n=scenario.grid_size,
        candidate_type=scenario.candidate_type.value,
    )

    if not sudoku_models:
        pytest.skip(f"Não há Sudokus cadastrados para {scenario.candidate_type}.")

    for attempt, sudoku_model in enumerate(sudoku_models, start=1):
        sudoku: Sudoku = SudokuMapper.to_sudoku(sudoku_model)
        verified_candidates: Tuple[SudokuCandidate, ...] = getattr(sudoku, scenario.verified_attr)

        assert verified_candidates, (
            f"O Sudoku id={getattr(sudoku_model, 'id', 'desconhecido')} "
            f"não possui candidatos para {scenario.label}. Revise o dataset."
        )

        result_schema = scenario.solver(sudoku_reasoner, sudoku)
        llm_response = SudokuCandidate(value=result_schema.value, position=result_schema.position)

        is_correct: bool = llm_response in verified_candidates
        SudokuRepository.update_inference_result(sudoku_model.id, is_correct)

        if is_correct:
            successes += 1
        else:
            failures.append(
                f"#{attempt} id={getattr(sudoku_model, 'id', 'desconhecido')} "
                f"esperado∈{verified_candidates}, obtido={llm_response}"
            )

    total_entries = len(sudoku_models)
    accuracy: float = successes / total_entries
    print(f"[{scenario.label}] acurácia: {accuracy:.2%} ({successes}/{total_entries})")

    if failures:
        preview = "\n".join(failures[:5])
        print(
            f"[WARN] {scenario.label} falhou em {len(failures)} de {total_entries} execuções "
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
