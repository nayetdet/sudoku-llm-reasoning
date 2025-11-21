from enum import Enum

class SudokuSimplifiedCandidateType(Enum):
    ZEROTH_LAYER_NAKED_SINGLES = "ZEROTH_LAYER_NAKED_SINGLES"
    ZEROTH_LAYER_HIDDEN_SINGLES = "ZEROTH_LAYER_HIDDEN_SINGLES"
    FIRST_LAYER_CONSENSUS = "FIRST_LAYER_CONSENSUS"

    @property
    def display_name(self) -> str:
        match self:
            case SudokuSimplifiedCandidateType.ZEROTH_LAYER_NAKED_SINGLES:
                return "Naked Singles (camada 0)"
            case SudokuSimplifiedCandidateType.ZEROTH_LAYER_HIDDEN_SINGLES:
                return "Hidden Singles (camada 0)"
            case SudokuSimplifiedCandidateType.FIRST_LAYER_CONSENSUS:
                return "Consensus (1ª camada)"

    @property
    def simplified_display_name(self) -> str:
        match self:
            case SudokuSimplifiedCandidateType.ZEROTH_LAYER_NAKED_SINGLES:
                return "naked_singles"
            case SudokuSimplifiedCandidateType.ZEROTH_LAYER_HIDDEN_SINGLES:
                return "hidden_singles"
            case SudokuSimplifiedCandidateType.FIRST_LAYER_CONSENSUS:
                return "consensus"
