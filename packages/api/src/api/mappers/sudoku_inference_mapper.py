from typing import Optional
from api.models.sudoku_inference import SudokuInference as SudokuInferenceModel
from api.schemas.responses.sudoku_inference_response_schema import SudokuInferenceResponseSchema

class SudokuInferenceMapper:
    @classmethod
    def to_inference(cls, sudoku_id: int, succeeded: bool, succeeded_nth_layer: bool, explanation: Optional[str]) -> SudokuInferenceModel:
        return SudokuInferenceModel(
            sudoku_id=sudoku_id,
            succeeded=succeeded,
            succeeded_nth_layer=succeeded_nth_layer,
            explanation=explanation
        )

    @classmethod
    def to_inference_response_schema(cls, inference: SudokuInferenceModel) -> SudokuInferenceResponseSchema:
        return SudokuInferenceResponseSchema(
            id=inference.id,
            succeeded=inference.succeeded,
            succeeded_nth_layer=inference.succeeded_nth_layer,
            explanation=inference.explanation
        )
