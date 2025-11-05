from typing import Optional, List
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Enum, JSON
from api.enums.sudoku_candidate_type import SudokuCandidateType

class Sudoku(SQLModel, table=True):
    __tablename__ = "sudoku"
    id: Optional[int] = Field(default=None, primary_key=True)
    n: int = Field(nullable=False)
    candidate_type: SudokuCandidateType = Field(sa_column=Column(Enum(SudokuCandidateType), nullable=False))
    grid: List[List[int]] = Field(sa_column=Column(JSON, nullable=False))
