from api.enums.sudoku_candidate_type import SudokuCandidateType
from api.models.sudoku import Sudoku as SudokuModel
from api.schemas.responses.sudoku_response_schema import SudokuResponseSchema
from core.sudoku import Sudoku

class SudokuMapper:
    @classmethod
    def to_sudoku(cls, sudoku_model: SudokuModel) -> Sudoku:
        return Sudoku(sudoku_model.grid)

    @classmethod
    def to_sudoku_model(cls, sudoku: Sudoku, candidate_type: SudokuCandidateType) -> SudokuModel:
        return SudokuModel(
            n=len(sudoku),
            candidate_type=candidate_type,
            grid=sudoku.grid
        )

    @classmethod
    def to_sudoku_response_schema(cls, sudoku_model: SudokuModel):
        return SudokuResponseSchema(
            n=sudoku_model.n,
            candidate_type=sudoku_model.candidate_type,
            grid=sudoku_model.grid
        )
