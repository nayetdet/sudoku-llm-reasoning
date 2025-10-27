from pathlib import Path

class Config:
    class Paths:
        ROOT: Path = Path.cwd()
        DATA: Path = ROOT / "data"
