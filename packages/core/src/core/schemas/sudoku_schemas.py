from typing import Tuple, List
from enum import Enum

from pydantic import BaseModel

class SudokuLLMCandidateSchema(BaseModel):
    value: int
    type: 'Technique'
    position: Tuple[int, int]
    explanation: str

class Technique(Enum):
    NAKED_SINGLES = 1
    HIDDEN_SINGLES = 2
    CONSENSUS_PRINCIPLE = 3