from typing import List, Tuple
from tabulate import tabulate
from api.repositories.sudoku_repository import SudokuRepository

class SudokuDBReader:
    @classmethod
    def read(cls) -> None:
        table: List[Tuple[int, int, str, List[List[int]]]] = []
        for sudoku in SudokuRepository.get_all():
            table.append((
                sudoku.id,
                sudoku.n,
                sudoku.candidate_type.value,
                sudoku.grid
            ))

        headers: Tuple[str, str, str, str] = "ID", "N", "Candidate Type", "Grid"
        print(tabulate(table, headers=headers, tablefmt="grid"))

def main() -> None:
    SudokuDBReader.read()

if __name__ == "__main__":
    main()
