from scripts.models.base_model import db
from scripts.models.sudoku_model import SudokuModel

def load_database() -> None:
    db.connect()
    db.create_tables([SudokuModel])
