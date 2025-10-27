from typing import List, Tuple
from tabulate import tabulate
from scripts.repositories.sudoku_model_repository import SudokuModelRepository

class SudokuDBReader:
    @classmethod
    def read(cls) -> None:
        table: List[Tuple[int, int, str, str]] = []
        for sudoku in SudokuModelRepository.get_all():
            table.append((
                sudoku.id,
                sudoku.n,
                sudoku.candidate_type,
                sudoku.grid
            ))

        headers: Tuple[str, str, str, str] = "ID", "N", "Candidate Type", "Grid"
        print(tabulate(table, headers=headers, tablefmt="grid"))

def main() -> None:
    SudokuDBReader.read()

if __name__ == "__main__":
    main()
