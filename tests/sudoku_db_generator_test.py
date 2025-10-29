from typing import List
from scripts.enums.sudoku_model_candidate_type import SudokuModelCandidateType
from scripts.mappers.sudoku_mapper import SudokuMapper
from scripts.models import SudokuModel
from scripts.repositories.sudoku_model_repository import SudokuModelRepository
from src.sudoku_llm_reasoning.core.sudoku import Sudoku

def test_naked_singles_sudoku() -> None:
    sudoku_models: List[SudokuModel] = SudokuModelRepository.get_all(candidate_type=SudokuModelCandidateType.ZEROTH_LAYER_NAKED_SINGLES)
    assert sudoku_models
    for sudoku_model in sudoku_models:
        sudoku: Sudoku = SudokuMapper.to_sudoku(sudoku_model)
        assert not sudoku.candidates_0th_layer_hidden_singles
        assert sudoku.candidates_0th_layer_naked_singles

def test_hidden_singles_sudoku() -> None:
    sudoku_models: List[SudokuModel] = SudokuModelRepository.get_all(candidate_type=SudokuModelCandidateType.ZEROTH_LAYER_HIDDEN_SINGLES)
    assert sudoku_models
    for sudoku_model in sudoku_models:
        sudoku: Sudoku = SudokuMapper.to_sudoku(sudoku_model)
        assert not sudoku.candidates_0th_layer_naked_singles
        assert sudoku.candidates_0th_layer_hidden_singles

def test_example_consensus_sudoku() -> None:
    sudoku: Sudoku = Sudoku([
        [2, 7, 1, 8, 9, 6, 0, 0, 0],
        [9, 4, 3, 5, 2, 7, 6, 8, 1],
        [8, 5, 6, 3, 1, 4, 7, 9, 2],
        [4, 8, 0, 0, 0, 0, 0, 2, 0],
        [6, 3, 0, 0, 0, 0, 0, 0, 0],
        [5, 1, 0, 0, 0, 0, 0, 0, 0],
        [3, 9, 5, 0, 0, 0, 0, 7, 0],
        [7, 2, 4, 0, 3, 8, 5, 0, 9],
        [1, 6, 8, 0, 0, 0, 2, 4, 3]
    ])

    assert not sudoku.candidates_0th_layer_naked_singles
    assert not sudoku.candidates_0th_layer_hidden_singles
    assert sudoku.candidates_1st_layer_consensus
    assert sudoku.candidates_1st_layer_consensus != sudoku.candidates_1st_layer_partial_consensus

def test_consensus_sudoku() -> None:
    sudoku_models: List[SudokuModel] = SudokuModelRepository.get_all(candidate_type=SudokuModelCandidateType.FIRST_LAYER_CONSENSUS)
    assert sudoku_models
    for sudoku_model in sudoku_models:
        sudoku: Sudoku = SudokuMapper.to_sudoku(sudoku_model)
        assert not sudoku.candidates_0th_layer_naked_singles
        assert not sudoku.candidates_0th_layer_hidden_singles
        assert sudoku.candidates_1st_layer_consensus
        assert sudoku.candidates_1st_layer_consensus != sudoku.candidates_1st_layer_partial_consensus
