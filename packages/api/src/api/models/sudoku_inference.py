from typing import Optional
from sqlalchemy import Column, Text, Boolean
from sqlmodel import SQLModel, Field, Relationship

class SudokuInference(SQLModel, table=True):
    __tablename__ = "sudoku_inference"
    id: Optional[int] = Field(default=None, primary_key=True)
    sudoku_id: int = Field(
        foreign_key="sudoku.id",
        index=True,
        sa_column_kwargs={
            "unique": True,
            "nullable": False
        }
    )
    succeeded: bool = Field(sa_column=Column(Boolean, nullable=False))
    succeeded_nth_layer: bool = Field(sa_column=Column(Boolean, nullable=False))
    explanation: Optional[str] = Field(sa_column=Column(Text, nullable=True))
    sudoku: "Sudoku" = Relationship(
        back_populates="inference",
        sa_relationship_kwargs={
            "uselist": False
        }
    )
