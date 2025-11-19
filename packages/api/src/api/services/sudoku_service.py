from typing import List, Optional, Literal, get_args
from api.deps.factory_instance import FactoryInstance
from api.exceptions.sudoku_exceptions import SudokuNotFoundException
from api.logger import logger
from api.mappers.sudoku_mapper import SudokuMapper
from api.models.sudoku import Sudoku as SudokuModel
from api.repositories.sudoku_repository import SudokuRepository
from api.schemas.queries.base_query_schema import PageSchema, PageableSchema
from api.schemas.queries.sudoku_query_schema import SudokuQuerySchema
from api.schemas.requests.sudoku_bulk_request_schema import SudokuBulkRequestSchema
from api.schemas.requests.sudoku_request_schema import SudokuRequestSchema
from api.schemas.responses.sudoku_response_schema import SudokuResponseSchema
from core.enums.sudoku_simplified_candidate_type import SudokuSimplifiedCandidateType
from core.factories.sudoku_factory import SudokuFactory

class SudokuService:
    @classmethod
    def get_all(cls, query: SudokuQuerySchema) -> PageSchema[SudokuResponseSchema]:
        content: List[SudokuModel] = SudokuRepository.get_all(n=query.n, candidate_type=query.candidate_type, page=query.page, size=query.size)
        total_elements: int = SudokuRepository.count(n=query.n, candidate_type=query.candidate_type)
        return PageSchema[SudokuResponseSchema](
            content=[SudokuMapper.to_sudoku_response_schema(x) for x in content],
            pageable=PageableSchema(
                page=query.page,
                size=query.size,
                total_elements=total_elements
            )
        )

    @classmethod
    def get_by_id(cls, sudoku_id: int) -> SudokuResponseSchema:
        sudoku: Optional[SudokuModel] = SudokuRepository.get_by_id(sudoku_id)
        if sudoku is None:
            raise SudokuNotFoundException()
        return SudokuMapper.to_sudoku_response_schema(sudoku)

    @classmethod
    def create_all(cls, request: SudokuBulkRequestSchema) -> None:
        for n in get_args(Literal[4, 9]):
            for candidate_type in SudokuSimplifiedCandidateType:
                cls.create(
                    SudokuMapper.to_sudoku_request_schema(
                        n=n,
                        candidate_type=candidate_type,
                        target_count=request.target_count,
                        max_attempts=request.max_attempts
                    )
                )

    @classmethod
    def create(cls, request: SudokuRequestSchema) -> None:
        successful_generations: int = 0
        factory: SudokuFactory = FactoryInstance.get_sudoku_factory(request.n)
        for sudoku in factory.get_sudokus_by_candidate_type(request.candidate_type, request.target_count, request.max_attempts):
            if sudoku is None:
                logger.info(f"{factory.n}x{factory.n} grid | {request.candidate_type.name}: Sudoku generation failed")
                continue
            if SudokuRepository.create(SudokuMapper.to_sudoku_model(sudoku, candidate_type=request.candidate_type)):
                successful_generations += 1
                logger.info(f"{factory.n}x{factory.n} grid | {request.candidate_type.name}: Sudoku generation succeeded ({successful_generations}/{request.target_count})")
                if successful_generations >= request.target_count:
                    break
            else: logger.info(f"{factory.n}x{factory.n} grid | {request.candidate_type.name}: Sudoku already exists, skipping")
        logger.info(f"Successfully generated {successful_generations}/{request.target_count} {factory.n}x{factory.n} grids for candidate type: {request.candidate_type.name}")

    @classmethod
    def delete_by_id(cls, sudoku_id: int) -> None:
        if not SudokuRepository.delete_by_id(sudoku_id):
            raise SudokuNotFoundException()
