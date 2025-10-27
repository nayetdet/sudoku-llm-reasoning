from peewee import Database, SqliteDatabase
from scripts.config import Config

db: Database = SqliteDatabase(Config.Paths.DATA / "sudoku.db")
