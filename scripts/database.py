from sqlalchemy import create_engine, event
from scripts.config import Config
from scripts.models import ModelBase

engine = create_engine(
    url=f"""sqlite:///{Config.Paths.DATA / "sudoku.db"}""",
    echo=False,
    connect_args={
        "timeout": 30
    }
)

ModelBase.metadata.create_all(engine)

@event.listens_for(engine, identifier="connect")
def set_sqlite_pragma(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.close()
