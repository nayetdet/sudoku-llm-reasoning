from sqlalchemy.orm import DeclarativeBase

class ModelBase(DeclarativeBase):
    pass

from .sudoku_model import SudokuModel
