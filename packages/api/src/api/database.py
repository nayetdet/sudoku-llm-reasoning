from pathlib import Path

from sqlalchemy import event
from sqlmodel import create_engine

from api.config import Config

DATABASE_FILE: Path = Config.Paths.DATA / "data.db"

engine = create_engine(
    url=f"sqlite:///{DATABASE_FILE}",
    echo=False,
    connect_args={
        "timeout": 30
    }
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.close()
