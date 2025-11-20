import itertools
from typing import Tuple
from sqlmodel import null
from api.deps.agent_instance import AgentInstance
from api.logger import logger
from api.mappers.sudoku_inference_mapper import SudokuInferenceMapper
from api.mappers.sudoku_mapper import SudokuMapper
from api.models.sudoku import Sudoku as SudokuModel
from api.repositories.sudoku_inference_repository import SudokuInferenceRepository
from api.repositories.sudoku_repository import SudokuRepository
from api.schemas.requests.sudoku_inference_request_schema import SudokuInferenceRequestSchema
from core.enums.sudoku_simplified_candidate_type import SudokuSimplifiedCandidateType
from core.exceptions.sudoku_inference_agent_exceptions import SudokuInferenceAgentGenerationException
from core.sudoku import Sudoku, SudokuCandidate
from core.sudoku_inference_agent import SudokuInferenceCandidate

class SudokuInferenceService:
    @classmethod
    def create(cls, request: SudokuInferenceRequestSchema) -> None:
        for n, candidate_type in itertools.product(request.ns, request.candidate_types):
            generated_inferences: int = 0
            for _ in range(request.target_count):
                sudoku_model: SudokuModel = SudokuRepository.get_random(n=n, candidate_type=candidate_type, inference_succeeded=null())
                if sudoku_model is None:
                    logger.info(f"{n}x{n} grid | {candidate_type.name}: No Sudoku available without inference")
                    break

                sudoku: Sudoku = SudokuMapper.to_sudoku(sudoku_model)
                try: llm_candidate: SudokuInferenceCandidate = AgentInstance.get_sudoku_inference_agent().solve(sudoku, candidate_type=candidate_type)
                except SudokuInferenceAgentGenerationException:
                    logger.error(f"{n}x{n} grid | {candidate_type.name}: LLM inference failed for sudoku_id={sudoku_model.id}")
                    continue

                candidates: Tuple[SudokuCandidate, ...] = ()
                match candidate_type:
                    case SudokuSimplifiedCandidateType.ZEROTH_LAYER_NAKED_SINGLES: candidates = sudoku.candidates_0th_layer_naked_singles
                    case SudokuSimplifiedCandidateType.ZEROTH_LAYER_HIDDEN_SINGLES: candidates = sudoku.candidates_0th_layer_hidden_singles
                    case SudokuSimplifiedCandidateType.FIRST_LAYER_CONSENSUS: candidates = sudoku.candidates_1st_layer_consensus

                generated_inferences += 1
                inference_succeeded: bool = llm_candidate.candidate in candidates
                logger.info(f"{n}x{n} grid | {candidate_type.name}: sudoku_id={sudoku_model.id} succeeded={inference_succeeded} ({generated_inferences}/{request.target_count})")
                SudokuInferenceRepository.create(
                    SudokuInferenceMapper.to_inference(
                        sudoku_id=sudoku_model.id,
                        succeeded=inference_succeeded,
                        explanation=llm_candidate.explanation
                    )
                )
