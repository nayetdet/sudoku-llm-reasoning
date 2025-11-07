import base64
from typing import Iterable, Any, Dict

from api.deps.serializer_instance import SerializerInstance
from api.enums.sudoku_candidate_type import SudokuCandidateType
from api.models.sudoku import Sudoku as SudokuModel
from api.models.sudoku_image import SudokuImage
from api.schemas.responses.sudoku_image_response_schema import SudokuImageResponseSchema
from api.schemas.responses.sudoku_response_schema import SudokuResponseSchema
from core.schemas.sudoku_schemas import SudokuLLMCandidateSchema
from core.sudoku import Sudoku, SudokuCandidate


class SudokuMapper:
    @classmethod
    def to_sudoku(cls, sudoku_model: SudokuModel) -> Sudoku:
        return Sudoku(sudoku_model.grid)

    @classmethod
    def to_sudoku_model(cls, sudoku: Sudoku, candidate_type: SudokuCandidateType) -> SudokuModel:
        image_payloads: Iterable[bytes] = SerializerInstance.get_sudoku_figure_serializer().serialize(sudoku, candidate_type)
        return SudokuModel(
            n=len(sudoku),
            candidate_type=candidate_type,
            grid=[list(x) for x in sudoku.grid],
            images=[
                SudokuImage(content=image_bytes, mime="image/png")
                for image_bytes in image_payloads
            ]
        )

    @classmethod
    def to_sudoku_candidate(cls, schema: SudokuLLMCandidateSchema) -> SudokuCandidate:
        return SudokuCandidate(
            value=schema.value,
            position=schema.position
        )

    @classmethod
    def to_llm_candidates_schema(cls, data: Dict[str, Any]) -> SudokuLLMCandidateSchema:
        return SudokuLLMCandidateSchema(
            position=data.get("position"),
            value=data.get("value"),
            explanation=data.get("explanation"),
            type=data.get("type"))

    @classmethod
    def to_sudoku_response_schema(cls, sudoku_model: SudokuModel) -> SudokuResponseSchema:
        return SudokuResponseSchema(
            id=sudoku_model.id,
            n=sudoku_model.n,
            candidate_type=sudoku_model.candidate_type,
            grid=sudoku_model.grid,
            images=[
                SudokuImageResponseSchema(
                    id=image.id,
                    mime=image.mime,
                    content_base64=base64.b64encode(image.content).decode("utf-8")
                )
                for image in (sudoku_model.images or [])
            ]
        )
