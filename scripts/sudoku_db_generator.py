import logging
from typing import Set, Optional
from scripts.enums.sudoku_model_candidate_type import SudokuModelCandidateType
from scripts.exceptions.sudoku_db_generator_exceptions import SudokuDBGeneratorNotEmptyException
from scripts.factories.sudoku_factory import SudokuFactory
from scripts.mappers.sudoku_mapper import SudokuMapper
from scripts.repositories.sudoku_model_repository import SudokuModelRepository
from src.sudoku_llm_reasoning.core.sudoku import Sudoku

class SudokuDBGenerator:
    MAX_GENERATION_ATTEMPTS: int = 50

    def __init__(self) -> None:
        self.__sudoku_factory_4x4: SudokuFactory = SudokuFactory(n=4)
        self.__sudoku_factory_9x9: SudokuFactory = SudokuFactory(n=9, max_solutions=10000)

    def generate(self) -> None:
        if SudokuModelRepository.count() > 0:
            raise SudokuDBGeneratorNotEmptyException("The database is not empty")

        for factory in (self.__sudoku_factory_4x4, self.__sudoku_factory_9x9):
            for candidate_type in SudokuModelCandidateType:
                logging.info(f"Generating {factory.n}x{factory.n} grid for candidate type: {candidate_type.name}")
                entries: Set[Sudoku] = set()

                for attempt in range(1, self.MAX_GENERATION_ATTEMPTS + 1):
                    entry: Optional[Sudoku] = factory.get_sudoku_by_candidate_type(candidate_type=candidate_type)
                    if entry is None:
                        logging.info(f"Attempt #{attempt}: Sudoku generation failed")
                        continue

                    if entry not in entries:
                        entries.add(entry)
                        SudokuModelRepository.create(SudokuMapper.to_sudoku_model(sudoku=entry, candidate_type=candidate_type))
                        logging.info(f"Attempt #{attempt}: Sudoku added to database ({len(entries)}/{self.MAX_GENERATION_ATTEMPTS})")
                    else: logging.info(f"Attempt #{attempt}: Sudoku already exists, skipping")

                if len(entries) < self.MAX_GENERATION_ATTEMPTS:
                    logging.warning(f"Could only generate {len(entries)}/{self.MAX_GENERATION_ATTEMPTS} {factory.n}x{factory.n} grids for candidate type: {candidate_type.name}")
                logging.info("")

def main() -> None:
    sudoku_db_generator: SudokuDBGenerator = SudokuDBGenerator()
    sudoku_db_generator.generate()

if __name__ == "__main__":
    main()
