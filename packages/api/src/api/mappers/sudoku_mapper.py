import base64
from typing import Any, Dict, List, Literal, Optional
from api.deps.serializer_instance import SerializerInstance
from api.models.sudoku import Sudoku as SudokuModel
from api.models.sudoku_image import SudokuImage as SudokuImageModel
from api.schemas.requests.sudoku_request_schema import SudokuRequestSchema
from api.schemas.responses.sudoku_image_response_schema import SudokuImageResponseSchema
from api.schemas.responses.sudoku_response_schema import SudokuResponseSchema
from core.enums.sudoku_simplified_candidate_type import SudokuSimplifiedCandidateType
from core.sudoku import Sudoku

class SudokuImageMapper:
    @classmethod
    def to_image(cls, content: bytes) -> SudokuImageModel:
        return SudokuImageModel(content=content, mime="image/png")

    @classmethod
    def to_image_response_schema(cls, image: SudokuImageModel) -> SudokuImageResponseSchema:
        return SudokuImageResponseSchema(
            id=image.id,
            content_base64=base64.b64encode(image.content).decode("utf-8"),
            mime=image.mime
        )

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
    def to_sudoku_request_schema(cls, n: Literal[4, 9], candidate_type: SudokuSimplifiedCandidateType, target_count: int, max_attempts: int) -> SudokuRequestSchema:
        return SudokuRequestSchema(
            n=n,
            candidate_type=candidate_type,
            target_count=target_count,
            max_attempts=max_attempts
        )

    @classmethod
    def to_sudoku_response_schema(cls, sudoku_model: SudokuModel) -> SudokuResponseSchema:
        return SudokuResponseSchema(
            id=sudoku_model.id,
            n=sudoku_model.n,
            candidate_type=sudoku_model.candidate_type,
            grid=sudoku_model.grid,
            inference_succeeded=sudoku_model.inference_succeeded,
            images=[
                SudokuImageMapper.to_image_response_schema(image)
                for image in (sudoku_model.images or [])
            ]
        )
