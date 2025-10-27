from typing import Tuple, Set
from scripts.enums.sudoku_model_candidate_type import SudokuModelCandidateType
from scripts.exceptions.sudoku_db_generator_exceptions import SudokuDBGeneratorNotEmptyException
from scripts.factories.sudoku_factory import SudokuFactory
from scripts.mappers.sudoku_mapper import SudokuMapper
from scripts.repositories.sudoku_model_repository import SudokuModelRepository
from src.sudoku_llm_reasoning.core.sudoku import Sudoku

class SudokuDBGenerator:
    MAX_GENERATION_ATTEMPTS: int = 1000

    def __init__(self) -> None:
        self.__sudoku_factory_4x4: SudokuFactory = SudokuFactory(n=4)
        self.__sudoku_factory_9x9: SudokuFactory = SudokuFactory(n=9, max_solutions=1000)

    def generate(self) -> None:
        if SudokuModelRepository.count() > 0:
            raise SudokuDBGeneratorNotEmptyException("The database is not empty.")

        sudoku_entries: Set[Tuple[Sudoku, SudokuModelCandidateType]] = set()
        for factory in (self.__sudoku_factory_4x4, self.__sudoku_factory_9x9):
            for candidate_type in SudokuModelCandidateType:
                for _ in range(self.MAX_GENERATION_ATTEMPTS):
                    sudoku: Sudoku = factory.get_sudoku_by_candidate_type(candidate_type=candidate_type)
                    sudoku_entry: Tuple[Sudoku, SudokuModelCandidateType] = sudoku, candidate_type
                    if sudoku is not None and sudoku_entry not in sudoku_entries:
                        sudoku_entries.add(sudoku_entry)
                        SudokuModelRepository.create(SudokuMapper.to_sudoku_model(*sudoku_entry))

def main() -> None:
    sudoku_db_generator: SudokuDBGenerator = SudokuDBGenerator()
    sudoku_db_generator.generate()

if __name__ == "__main__":
    main()
