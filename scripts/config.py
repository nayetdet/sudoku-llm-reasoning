from pathlib import Path

class Config:
    class Paths:
        ROOT: Path = Path(__file__).resolve().parents[1]
        DATA: Path = ROOT / "data"
