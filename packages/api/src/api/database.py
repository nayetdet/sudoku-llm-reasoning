from pathlib import Path

from sqlalchemy import event
from sqlalchemy.engine import Connection
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


def ensure_sudoku_columns() -> None:
    """Add recent sudoku columns if they are missing in the file."""
    with engine.begin() as connection:
        columns = _fetch_table_columns(connection, "sudoku")
        if columns is None:
            return

        if "llm_is_correct" not in columns:
            connection.exec_driver_sql("ALTER TABLE sudoku ADD COLUMN llm_is_correct BOOLEAN")

        if "llm_checked_at" not in columns:
            connection.exec_driver_sql("ALTER TABLE sudoku ADD COLUMN llm_checked_at DATETIME")


def _fetch_table_columns(connection: Connection, table_name: str) -> set[str] | None:
    cursor = connection.exec_driver_sql(f"PRAGMA table_info({table_name})")
    rows = cursor.fetchall()
    if not rows:
        return None
    return {row[1] for row in rows}

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.close()


ensure_sudoku_columns()
