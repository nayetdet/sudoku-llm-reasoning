from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, LargeBinary, String

if TYPE_CHECKING:
    from api.models.sudoku import Sudoku

class SudokuImage(SQLModel, table=True):
    __tablename__ = "sudoku_image"
    id: Optional[int] = Field(default=None, primary_key=True)
    sudoku_id: int = Field(foreign_key="sudoku.id", index=True)
    content: Optional[bytes] = Field(sa_column=Column(LargeBinary, nullable=True))
    mime: str = Field(default="image/png", sa_column=Column(String(64), nullable=False))
    sudoku: "Sudoku" = Relationship(back_populates="images")
