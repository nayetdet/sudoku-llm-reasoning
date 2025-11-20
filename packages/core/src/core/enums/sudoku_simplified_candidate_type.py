from enum import Enum

class SudokuSimplifiedCandidateType(Enum):
    ZEROTH_LAYER_NAKED_SINGLES = "ZEROTH_LAYER_NAKED_SINGLES"
    ZEROTH_LAYER_HIDDEN_SINGLES = "ZEROTH_LAYER_HIDDEN_SINGLES"
    FIRST_LAYER_CONSENSUS = "FIRST_LAYER_CONSENSUS"

    @property
    def display_name(self) -> str:
        match self:
            case self.ZEROTH_LAYER_NAKED_SINGLES:
                return "Naked Singles"
            case self.ZEROTH_LAYER_HIDDEN_SINGLES:
                return "Hidden Singles"
            case self.FIRST_LAYER_CONSENSUS:
                return "Consensus"
