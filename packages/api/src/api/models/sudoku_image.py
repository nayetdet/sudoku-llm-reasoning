from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, LargeBinary, String

class SudokuImage(SQLModel, table=True):
    __tablename__ = "sudoku_image"
    id: Optional[int] = Field(default=None, primary_key=True)
    sudoku_id: int = Field(foreign_key="sudoku.id", index=True)
    content: bytes = Field(sa_column=Column(LargeBinary, nullable=False))
    mime: str = Field(default="image/png", sa_column=Column(String(length=64), nullable=False))
    sudoku: "Sudoku" = Relationship(back_populates="images")
