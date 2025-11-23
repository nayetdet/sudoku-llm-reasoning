from typing import Dict, Any
from core.enums.sudoku_simplified_candidate_type import SudokuSimplifiedCandidateType
from webui.components.shared.filter_component import FilterComponent, Filter

class SudokuFilterComponent:
    @classmethod
    def render(cls, session_key_prefix: str, expanded: bool = False) -> Dict[str, Any]:
        return FilterComponent.render(
            session_key_prefix=session_key_prefix,
            filters=[
                Filter(
                    key="n",
                    label="Grid Size (N)",
                    options=[None, 4, 9],
                    format_func=lambda x: str(x) if x else "All"
                ),
                Filter(
                    key="candidate_type",
                    label="Candidate Type",
                    options=[None] + [x.value for x in SudokuSimplifiedCandidateType],
                    format_func=lambda x: SudokuSimplifiedCandidateType(x).display_name if x is not None else "All"
                )
            ],
            expanded=expanded
        )
