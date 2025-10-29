from scripts.enums.sudoku_model_candidate_type import SudokuModelCandidateType
from scripts.mappers.sudoku_mapper import SudokuMapper
from scripts.models import SudokuModel
from scripts.repositories.sudoku_model_repository import SudokuModelRepository
from src.sudoku_llm_reasoning.core.sudoku import Sudoku
from src.sudoku_llm_reasoning.core.sudoku_reasoner import SudokuReasoner

def test_naked_singles_analysis(sudoku_reasoner: SudokuReasoner) -> None:
    sudoku_model: SudokuModel = SudokuModelRepository.get_random(candidate_type=SudokuModelCandidateType.ZEROTH_LAYER_NAKED_SINGLES.value)
    sudoku: Sudoku = SudokuMapper.to_sudoku(sudoku_model)
    sudoku_reasoner.analyze(sudoku)

def test_hidden_singles_analysis(sudoku_reasoner: SudokuReasoner) -> None:
    sudoku_model: SudokuModel = SudokuModelRepository.get_random(candidate_type=SudokuModelCandidateType.ZEROTH_LAYER_HIDDEN_SINGLES.value)
    sudoku: Sudoku = SudokuMapper.to_sudoku(sudoku_model)
    sudoku_reasoner.analyze(sudoku)

def test_consensus_analysis(sudoku_reasoner: SudokuReasoner) -> None:
    sudoku_model: SudokuModel = SudokuModelRepository.get_random(n=9, candidate_type=SudokuModelCandidateType.FIRST_LAYER_CONSENSUS.value)
    sudoku: Sudoku = SudokuMapper.to_sudoku(sudoku_model)
    sudoku_reasoner.analyze(sudoku)
