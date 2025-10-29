from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column
from scripts.models import ModelBase
from sqlalchemy import Enum, Text
from scripts.enums.sudoku_model_candidate_type import SudokuModelCandidateType

class SudokuModel(ModelBase):
    __tablename__ = "sudoku_model"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    n: Mapped[int] = mapped_column(Integer, nullable=False)
    candidate_type: Mapped[SudokuModelCandidateType] = mapped_column(Enum(SudokuModelCandidateType), nullable=False)
    grid: Mapped[str] = mapped_column(Text, nullable=False)
