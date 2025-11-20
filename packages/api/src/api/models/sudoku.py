from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Enum, JSON, Boolean, DateTime
from api.models.sudoku_image import SudokuImage
from api.models.sudoku_inference import SudokuInference
from core.enums.sudoku_simplified_candidate_type import SudokuSimplifiedCandidateType

class Sudoku(SQLModel, table=True):
    __tablename__ = "sudoku"
    id: Optional[int] = Field(default=None, primary_key=True)
    n: int = Field(nullable=False)
    candidate_type: SudokuSimplifiedCandidateType = Field(sa_column=Column(Enum(SudokuSimplifiedCandidateType), nullable=False))
    grid: List[List[int]] = Field(sa_column=Column(JSON, nullable=False))
    inference: Optional[SudokuInference] = Relationship(
        back_populates="sudoku",
        sa_relationship_kwargs={
            "uselist": False,
            "cascade": "all, delete-orphan",
            "passive_deletes": True,
            "lazy": "joined"
        }
    )
    images: List[SudokuImage] = Relationship(
        back_populates="sudoku",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "passive_deletes": True,
            "lazy": "joined"
        }
    )
