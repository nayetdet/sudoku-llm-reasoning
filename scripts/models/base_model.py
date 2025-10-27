from peewee import Model
from scripts.database import db

class BaseModel(Model):
    class Meta:
        database = db
