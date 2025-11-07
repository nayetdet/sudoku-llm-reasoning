
from api.mappers.sudoku_mapper import SudokuMapper
from api.repositories.sudoku_repository import SudokuRepository
from core.enums.sudoku_candidate_type import SudokuCandidateType
from core.sudoku import Sudoku
from core.sudoku_reasoner import SudokuReasoner

def test_consensus_analysis(sudoku_reasoner: SudokuReasoner) -> None:
    sudoku_model: Sudoku = SudokuRepository.get_random(n=9, candidate_type=SudokuCandidateType.FIRST_LAYER_CONSENSUS.value)
    sudoku: Sudoku = SudokuMapper.to_sudoku(sudoku_model)
    result = sudoku_reasoner.solve_consensus_principle(sudoku)

    llm_response = SudokuMapper.to_sudoku_candidate(result)
    verified_responses = sudoku.candidates_1st_layer_consensus

    assert llm_response in verified_responses
