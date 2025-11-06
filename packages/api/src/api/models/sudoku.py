from typing import List
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Enum, JSON
from api.enums.sudoku_candidate_type import SudokuCandidateType
from api.models.sudoku_image import SudokuImage

class Sudoku(SQLModel, table=True):
    __tablename__ = "sudoku"
    id: int = Field(default=None, primary_key=True)
    n: int = Field(nullable=False)
    candidate_type: SudokuCandidateType = Field(sa_column=Column(Enum(SudokuCandidateType), nullable=False))
    grid: List[List[int]] = Field(sa_column=Column(JSON, nullable=False))
    images: List[SudokuImage] = Relationship(
        back_populates="sudoku",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "passive_deletes": True
        }
    )
