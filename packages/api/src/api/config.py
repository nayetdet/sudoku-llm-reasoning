from pathlib import Path
from os import getenv
from typing import List

class Config:
    class API:
        CORS_ORIGINS: List[str] = [x.strip() for x in (getenv("API_CORS_ORIGINS") or "").split(",") if x.strip()]

        class Sudoku:
            MAX_SOLUTIONS: int = int(getenv("API_SUDOKU_MAX_SOLUTIONS") or 1000)
            NAKED_SINGLES_MIN_RATIO: float = float(getenv("API_SUDOKU_NAKED_SINGLES_MIN_RATIO") or 0.25)

    class Paths:
        ROOT: Path = Path(__file__).resolve().parents[2]
        DATA: Path = ROOT / "data"
