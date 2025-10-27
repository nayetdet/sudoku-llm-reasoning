import random
from typing import List, Optional
from scripts.enums.sudoku_model_candidate_type import SudokuModelCandidateType
from scripts.models import SudokuModel

class SudokuModelRepository:
    @classmethod
    def get_all(cls, n: Optional[int] = None, candidate_type: Optional[SudokuModelCandidateType] = None) -> List[SudokuModel]:
        query = SudokuModel.select()
        if n is not None:
            query = query.where(SudokuModel.n == n)
        if candidate_type is not None:
            query = query.where(SudokuModel.candidate_type == candidate_type.value)
        return list(query)

    @classmethod
    def get_random(cls, n: int, candidate_type: SudokuModelCandidateType) -> Optional[SudokuModel]:
        entries: List[SudokuModel] = cls.get_all(n=n, candidate_type=candidate_type)
        if not entries:
            return None
        return random.choice(entries)

    @classmethod
    def create(cls, sudoku_model: SudokuModel) -> SudokuModel:
        return sudoku_model.create()

    @classmethod
    def count(cls) -> int:
        return SudokuModel.select().count()
