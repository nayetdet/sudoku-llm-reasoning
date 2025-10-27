from peewee import IntegerField, TextField
from scripts.models.base_model import BaseModel

class SudokuModel(BaseModel):
    n = IntegerField()
    candidate_type = TextField()
    grid = TextField()
