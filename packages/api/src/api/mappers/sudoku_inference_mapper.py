from typing import Optional
from api.models.sudoku_inference import SudokuInference as SudokuInferenceModel
from api.schemas.responses.sudoku_inference_analytics_response_schema import SudokuInferenceAnalyticsResponseSchema
from api.schemas.responses.sudoku_inference_response_schema import SudokuInferenceResponseSchema
from core.enums.sudoku_simplified_candidate_type import SudokuSimplifiedCandidateType

class SudokuInferenceMapper:
    @classmethod
    def to_inference(cls, sudoku_id: int, succeeded: bool, succeeded_nth_layer: bool, succeeded_and_unique_nth_layer: bool, explanation: Optional[str]) -> SudokuInferenceModel:
        return SudokuInferenceModel(
            sudoku_id=sudoku_id,
            succeeded=succeeded,
            succeeded_nth_layer=succeeded_nth_layer,
            succeeded_and_unique_nth_layer=succeeded_and_unique_nth_layer,
            explanation=explanation
        )

    @classmethod
    def to_inference_response_schema(cls, inference: SudokuInferenceModel) -> SudokuInferenceResponseSchema:
        return SudokuInferenceResponseSchema(
            id=inference.id,
            succeeded=inference.succeeded,
            succeeded_nth_layer=inference.succeeded_nth_layer,
            succeeded_and_unique_nth_layer=inference.succeeded_and_unique_nth_layer,
            explanation=inference.explanation
        )

    @classmethod
    def to_inference_analytics_response_schema(
            cls,
            n: int,
            candidate_type: SudokuSimplifiedCandidateType,
            total_predicted: int,
            total_beyond: int,
            total_beyond_non_unique: int,
            total_hallucinations: int,
            total_missed: int,
            total_unprocessed: int,
            total: int
    ) -> SudokuInferenceAnalyticsResponseSchema:
        return SudokuInferenceAnalyticsResponseSchema(
            n=n,
            candidate_type=candidate_type,
            total_predicted=total_predicted,
            total_beyond=total_beyond,
            total_beyond_non_unique=total_beyond_non_unique,
            total_hallucinations=total_hallucinations,
            total_missed=total_missed,
            total_unprocessed=total_unprocessed,
            total=total
        )
