import pytest
from scripts.enums.sudoku_model_candidate_type import SudokuModelCandidateType
from scripts.mappers.sudoku_mapper import SudokuMapper
from scripts.repositories.sudoku_model_repository import SudokuModelRepository
from src.sudoku_llm_reasoning.core.sudoku import Sudoku

def test_naked_singles_sudoku() -> None:
    for sudoku_model in SudokuModelRepository.get_all(candidate_type=SudokuModelCandidateType.ZEROTH_LAYER_NAKED_SINGLES):
        sudoku: Sudoku = SudokuMapper.to_sudoku(sudoku_model)
        assert not sudoku.candidates_0th_layer_hidden_singles
        assert sudoku.candidates_0th_layer_naked_singles

def test_hidden_singles_sudoku() -> None:
    for sudoku_model in SudokuModelRepository.get_all(candidate_type=SudokuModelCandidateType.ZEROTH_LAYER_HIDDEN_SINGLES):
        sudoku: Sudoku = SudokuMapper.to_sudoku(sudoku_model)
        assert not sudoku.candidates_0th_layer_naked_singles
        assert sudoku.candidates_0th_layer_hidden_singles

@pytest.mark.skip
def test_consensus_sudoku() -> None:
    for sudoku_model in SudokuModelRepository.get_all(candidate_type=SudokuModelCandidateType.FIRST_LAYER_CONSENSUS):
        sudoku: Sudoku = SudokuMapper.to_sudoku(sudoku_model)
        assert not sudoku.candidates_0th_layer_naked_singles
        assert not sudoku.candidates_0th_layer_hidden_singles
        assert sudoku.candidates_1st_layer_consensus
        assert sudoku.candidates_1st_layer_consensus != sudoku.candidates_1st_layer_partial_consensus
