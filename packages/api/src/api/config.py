from pathlib import Path
from os import getenv
from typing import List

class Config:
    class API:
        CORS_ORIGINS: List[str] = [x.strip() for x in (getenv("API_CORS_ORIGINS") or "").split(",") if x.strip()]

        class Sudoku:
            DEFAULT_MAX_SOLUTIONS: int = int(getenv("API_SUDOKU_DEFAULT_MAX_SOLUTIONS") or 1000)
            DEFAULT_TARGET_COUNT: int = int(getenv("API_SUDOKU_DEFAULT_TARGET_COUNT") or 150)
            DEFAULT_MAX_ATTEMPTS: int = int(getenv("API_SUDOKU_DEFAULT_MAX_ATTEMPTS") or 1000)

    class LLM:
        MODEL: str = getenv("LLM_MODEL")
        API_KEY: str = getenv("LLM_API_KEY")

    class Paths:
        ROOT: Path = Path(__file__).resolve().parents[2]
        DATA: Path = ROOT / "data"
