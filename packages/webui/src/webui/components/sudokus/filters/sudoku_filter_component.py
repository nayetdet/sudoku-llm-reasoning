from typing import Dict, Any, Set, Optional
from core.enums.sudoku_simplified_candidate_type import SudokuSimplifiedCandidateType
from webui.components.shared.filter_component import FilterComponent, Filter

class SudokuFilterComponent:
    @classmethod
    def render(cls, session_key_prefix: str, filters: Optional[Set[str]] = None) -> Dict[str, Any]:
        available_filters: Dict[str, Any] = {
            "n": Filter(
                key="n",
                label="Grid Size (N)",
                options=[None, 4, 9],
                format_func=lambda x: str(x) if x is not None else "All"
            ),
            "candidate_type": Filter(
                key="candidate_type",
                label="Candidate Type",
                options=[None] + [x.value for x in SudokuSimplifiedCandidateType],
                format_func=lambda x: SudokuSimplifiedCandidateType(x).display_name if x is not None else "All"
            ),
            "inference_succeeded": Filter(
                key="inference_succeeded",
                label="Inference Succeeded",
                options=[None, True, False],
                format_func=lambda x: str(x) if x is not None else "All"
            ),
            "inference_succeeded_nth_layer": Filter(
                key="inference_succeeded_nth_layer",
                label="Inference Succeeded (Nth Layer)",
                options=[None, True, False],
                format_func=lambda x: str(x) if x is not None else "All"
            ),
            "inference_has_explanation": Filter(
                key="inference_has_explanation",
                label="Inference Has Explanation",
                options=[None, True, False],
                format_func=lambda x: str(x) if x is not None else "All"
            )
        }

        return FilterComponent.render(
            session_key_prefix=session_key_prefix,
            filters=[v for k, v in available_filters.items() if k in (filters or available_filters.keys())]
        )
