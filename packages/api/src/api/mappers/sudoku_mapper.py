from api.deps.serializer_instance import SerializerInstance
from api.mappers.sudoku_image_mapper import SudokuImageMapper
from api.mappers.sudoku_inference_mapper import SudokuInferenceMapper
from api.models.sudoku import Sudoku as SudokuModel
from api.schemas.responses.sudoku_response_schema import SudokuResponseSchema
from core.enums.sudoku_simplified_candidate_type import SudokuSimplifiedCandidateType
from core.sudoku import Sudoku

class SudokuMapper:
    @classmethod
    def to_sudoku(cls, sudoku_model: SudokuModel) -> Sudoku:
        return Sudoku(sudoku_model.grid)

    @classmethod
    def to_sudoku_model(cls, sudoku: Sudoku, candidate_type: SudokuSimplifiedCandidateType) -> SudokuModel:
        return SudokuModel(
            n=len(sudoku),
            candidate_type=candidate_type,
            grid=[list(x) for x in sudoku.grid],
            images=[
                SudokuImageMapper.to_image(content=content)
                for content in SerializerInstance.get_sudoku_figure_serializer().serialize(sudoku, candidate_type)
            ]
        )

    @classmethod
    def to_sudoku_response_schema(cls, sudoku_model: SudokuModel) -> SudokuResponseSchema:
        return SudokuResponseSchema(
            id=sudoku_model.id,
            n=sudoku_model.n,
            candidate_type=sudoku_model.candidate_type,
            grid=sudoku_model.grid,
            inference=SudokuInferenceMapper.to_inference_response_schema(sudoku_model.inference) if sudoku_model.inference else None
        )
