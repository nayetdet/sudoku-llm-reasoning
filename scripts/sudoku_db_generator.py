import logging
import os
from collections import defaultdict
from concurrent.futures import Future, as_completed
from concurrent.futures.process import ProcessPoolExecutor
from typing import Optional, List, Tuple, Dict
from scripts.enums.sudoku_model_candidate_type import SudokuModelCandidateType
from scripts.factories.sudoku_factory import SudokuFactory
from scripts.mappers.sudoku_mapper import SudokuMapper
from scripts.models import SudokuModel
from scripts.repositories.sudoku_model_repository import SudokuModelRepository
from src.sudoku_llm_reasoning.core.sudoku import Sudoku

class SudokuDBGenerator:
    __MAX_GENERATION_ATTEMPTS: int = 150

    def __init__(self) -> None:
        self.__factories: Dict[int, SudokuFactory] = {
            factory.n: factory
            for factory in [
                SudokuFactory(n=4),
                SudokuFactory(n=9, max_solutions=1000)
            ]
        }

    def generate(self) -> None:
        tasks: List[Tuple[int, int, SudokuModelCandidateType]] = []
        for n in self.__factories.keys():
            for candidate_type in SudokuModelCandidateType:
                for attempt in range(1, self.__MAX_GENERATION_ATTEMPTS + 1):
                    tasks.append((attempt, n, candidate_type))

        successful_generations: Dict[Tuple[int, SudokuModelCandidateType], int] = defaultdict(int)
        with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
            futures: Dict[Future[Optional[SudokuModel]], Tuple[int, int, SudokuModelCandidateType]] = {
                executor.submit(self._generate_single, n, candidate_type): (attempt, n, candidate_type)
                for attempt, n, candidate_type in tasks
            }

            for future in as_completed(futures):
                attempt, n, candidate_type = futures[future]
                try:
                    model: Optional[SudokuModel] = future.result()
                    if model is None:
                        logging.info(f"Attempt #{attempt:03d} ({n}x{n} grid | {candidate_type.name}): Sudoku generation failed")
                        continue

                    if SudokuModelRepository.create(model):
                        successful_generations[(n, candidate_type)] += 1
                        logging.info(f"Attempt #{attempt:03d} ({n}x{n} grid | {candidate_type.name}): Sudoku generation succeeded ({successful_generations[(n, candidate_type)]}/{self.__MAX_GENERATION_ATTEMPTS})")
                    else: logging.info(f"Attempt #{attempt:03d} ({n}x{n} grid | {candidate_type.name}): Sudoku already exists, skipping")
                except Exception as e:
                    logging.error(f"Attempt #{attempt:03d} ({n}x{n} grid | {candidate_type.name}): Error — {e}")

    def _generate_single(self, n: int, candidate_type: SudokuModelCandidateType) -> Optional[SudokuModel]:
        factory: SudokuFactory = self.__factories[n]
        sudoku: Optional[Sudoku] = factory.get_sudoku_by_candidate_type(candidate_type=candidate_type)
        if sudoku is None:
            return None
        return SudokuMapper.to_sudoku_model(sudoku=sudoku, candidate_type=candidate_type)

def main() -> None:
    sudoku_db_generator: SudokuDBGenerator = SudokuDBGenerator()
    sudoku_db_generator.generate()

if __name__ == "__main__":
    main()
