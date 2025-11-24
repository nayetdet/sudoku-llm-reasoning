import itertools
from typing import List, Tuple, Optional
from sqlmodel import null
from api.deps.agent_instance import AgentInstance
from api.exceptions.sudoku_inference_exceptions import SudokuInferenceNotFoundException
from api.logger import logger
from api.mappers.sudoku_inference_mapper import SudokuInferenceMapper
from api.mappers.sudoku_mapper import SudokuMapper
from api.models.sudoku import Sudoku as SudokuModel
from api.repositories.sudoku_inference_repository import SudokuInferenceRepository
from api.repositories.sudoku_repository import SudokuRepository
from api.schemas.requests.sudoku_inference_request_schema import SudokuInferenceRequestSchema
from api.schemas.responses.sudoku_inference_analytics_response_schema import SudokuInferenceAnalyticsResponseSchema
from core.enums.sudoku_simplified_candidate_type import SudokuSimplifiedCandidateType
from core.exceptions.sudoku_inference_agent_exceptions import SudokuInferenceAgentGenerationException
from core.sudoku import Sudoku, SudokuCandidate
from core.sudoku_inference_agent import SudokuInferenceCandidate

class SudokuInferenceService:
    @classmethod
    def get_analytics(cls) -> List[SudokuInferenceAnalyticsResponseSchema]:
        content: List[SudokuInferenceAnalyticsResponseSchema] = []
        for n, candidate_type in itertools.product(SudokuRepository.get_distinct_ns(), SudokuRepository.get_distinct_candidate_types()):
            content.append(
                SudokuInferenceMapper.to_inference_analytics_response_schema(
                    n=n,
                    candidate_type=candidate_type,
                    total_predicted=SudokuRepository.count(n=n, candidate_type=candidate_type, inference_succeeded=True, inference_succeeded_nth_layer=True),
                    total_beyond=SudokuRepository.count(n=n, candidate_type=candidate_type, inference_succeeded=False, inference_succeeded_nth_layer=True, inference_succeeded_and_unique_nth_layer=True),
                    total_beyond_non_unique=SudokuRepository.count(n=n, candidate_type=candidate_type, inference_succeeded=False, inference_succeeded_nth_layer=True, inference_succeeded_and_unique_nth_layer=False),
                    total_hallucinations=SudokuRepository.count(n=n, candidate_type=candidate_type, inference_succeeded=False, inference_succeeded_nth_layer=False, inference_has_explanation=True),
                    total_missed=SudokuRepository.count(n=n, candidate_type=candidate_type, inference_succeeded=False, inference_succeeded_nth_layer=False, inference_has_explanation=False),
                    total_unprocessed=SudokuRepository.count(n=n, candidate_type=candidate_type, inference_succeeded=null(), inference_succeeded_nth_layer=null()),
                    total=SudokuRepository.count(n=n, candidate_type=candidate_type)
                )
            )
        return content

    @classmethod
    def create(cls, request: SudokuInferenceRequestSchema) -> None:
        for n, candidate_type in itertools.product(request.ns, request.candidate_types):
            generated_inferences: int = 0
            for _ in range(request.target_count):
                sudoku_model: SudokuModel = SudokuRepository.get_random(
                    n=n,
                    candidate_type=candidate_type,
                    inference_succeeded=null(),
                    inference_succeeded_nth_layer=null()
                )

                if sudoku_model is None:
                    logger.info(f"{n}x{n} grid | {candidate_type.name}: No Sudoku available without inference")
                    break

                sudoku: Sudoku = SudokuMapper.to_sudoku(sudoku_model)
                try: llm_candidate: Optional[SudokuInferenceCandidate] = AgentInstance.get_sudoku_inference_agent().solve(sudoku, candidate_type=candidate_type)
                except SudokuInferenceAgentGenerationException:
                    logger.error(f"{n}x{n} grid | {candidate_type.name}: LLM inference failed for sudoku_id={sudoku_model.id}")
                    continue

                inference_succeeded: bool = False
                inference_succeeded_nth_layer: bool = False
                inference_succeeded_and_unique_nth_layer: bool = False
                if llm_candidate is not None:
                    candidates: Tuple[SudokuCandidate, ...] = ()
                    match candidate_type:
                        case SudokuSimplifiedCandidateType.ZEROTH_LAYER_NAKED_SINGLES: candidates = sudoku.candidates_0th_layer_naked_singles
                        case SudokuSimplifiedCandidateType.ZEROTH_LAYER_HIDDEN_SINGLES: candidates = sudoku.candidates_0th_layer_hidden_singles
                        case SudokuSimplifiedCandidateType.FIRST_LAYER_CONSENSUS: candidates = sudoku.candidates_1st_layer_consensus
                    inference_succeeded = inference_succeeded_nth_layer = llm_candidate.candidate in candidates
                    inference_succeeded_nth_layer = inference_succeeded or llm_candidate.candidate in sudoku.candidates_nth_layer
                    inference_succeeded_and_unique_nth_layer = inference_succeeded_nth_layer and len(sudoku.candidate_values_nth_layer_at_position(*llm_candidate.position)) == 1

                generated_inferences += 1
                logger.info(f"{n}x{n} grid | {candidate_type.name}: sudoku_id={sudoku_model.id} succeeded={inference_succeeded} succeeded_nth_layer={inference_succeeded_nth_layer} ({generated_inferences}/{request.target_count})")
                SudokuInferenceRepository.create(
                    SudokuInferenceMapper.to_inference(
                        sudoku_id=sudoku_model.id,
                        succeeded=inference_succeeded,
                        succeeded_nth_layer=inference_succeeded_nth_layer,
                        succeeded_and_unique_nth_layer=inference_succeeded_and_unique_nth_layer,
                        explanation=llm_candidate.explanation if llm_candidate is not None else None
                    )
                )

    @classmethod
    def delete_by_id(cls, inference_id: int) -> None:
        if not SudokuInferenceRepository.delete_by_id(inference_id):
            raise SudokuInferenceNotFoundException()
