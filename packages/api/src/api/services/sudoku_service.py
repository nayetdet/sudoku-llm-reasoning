import itertools
from typing import Optional
from api.deps.factory_instance import FactoryInstance
from api.exceptions.sudoku_exceptions import SudokuNotFoundException
from api.logger import logger
from api.mappers.sudoku_mapper import SudokuMapper
from api.models.sudoku import Sudoku as SudokuModel
from api.repositories.sudoku_repository import SudokuRepository
from api.schemas.queries.base_query_schema import PageSchema, PageableSchema
from api.schemas.queries.sudoku_query_schema import SudokuQuerySchema
from api.schemas.requests.sudoku_request_schema import SudokuRequestSchema
from api.schemas.responses.sudoku_response_schema import SudokuResponseSchema
from core.factories.sudoku_factory import SudokuFactory

class SudokuService:
    @classmethod
    def get_all(cls, query: SudokuQuerySchema) -> PageSchema[SudokuResponseSchema]:
        return PageSchema[SudokuResponseSchema](
            content=[
                SudokuMapper.to_sudoku_response_schema(model)
                for model in SudokuRepository.get_all(
                    n=query.n,
                    candidate_type=query.candidate_type,
                    inference_succeeded=query.inference_succeeded,
                    page=query.page,
                    size=query.size
                )
            ],
            pageable=PageableSchema(
                page=query.page,
                size=query.size,
                total_elements=SudokuRepository.count(
                    n=query.n,
                    candidate_type=query.candidate_type,
                    inference_succeeded=query.inference_succeeded,
                    inference_succeeded_nth_layer=query.inference_succeeded_nth_layer
                )
            )
        )

    @classmethod
    def get_by_id(cls, sudoku_id: int) -> SudokuResponseSchema:
        sudoku: Optional[SudokuModel] = SudokuRepository.get_by_id(sudoku_id)
        if sudoku is None:
            raise SudokuNotFoundException()
        return SudokuMapper.to_sudoku_response_schema(sudoku)

    @classmethod
    def create(cls, request: SudokuRequestSchema) -> None:
        for n, candidate_type in itertools.product(request.ns, request.candidate_types):
            successful_generations: int = 0
            factory: SudokuFactory = FactoryInstance.get_sudoku_factory(n)
            for sudoku in factory.get_sudokus_by_candidate_type(candidate_type, request.target_count, request.max_attempts):
                if sudoku is None:
                    logger.info(f"{factory.n}x{factory.n} grid | {candidate_type.name}: Sudoku generation failed")
                    continue

                if SudokuRepository.create(SudokuMapper.to_sudoku_model(sudoku, candidate_type=candidate_type)):
                    successful_generations += 1
                    logger.info(f"{factory.n}x{factory.n} grid | {candidate_type.name}: Sudoku generation succeeded ({successful_generations}/{request.target_count})")
                    if successful_generations >= request.target_count:
                        break
                else: logger.info(f"{factory.n}x{factory.n} grid | {candidate_type.name}: Sudoku already exists, skipping")
            logger.info(f"Successfully generated {successful_generations}/{request.target_count} {factory.n}x{factory.n} grids for candidate type: {candidate_type.name}")

    @classmethod
    def delete_by_id(cls, sudoku_id: int) -> None:
        if not SudokuRepository.delete_by_id(sudoku_id):
            raise SudokuNotFoundException()
