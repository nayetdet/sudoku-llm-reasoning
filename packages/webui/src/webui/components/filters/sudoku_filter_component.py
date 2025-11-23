import streamlit as st
from typing import Dict, Any
from core.enums.sudoku_simplified_candidate_type import SudokuSimplifiedCandidateType

class SudokuFilterComponent:
    @classmethod
    def render(cls, session_key_prefix: str, expanded: bool = False) -> Dict[str, Any]:
        form_key: str = f"{session_key_prefix}_filters_form_key"
        filters_key: str = f"{session_key_prefix}_filters"

        st.session_state.setdefault(form_key, 0)
        st.session_state.setdefault(filters_key, {})
        with st.expander("Filters", expanded=expanded):
            with st.form(f"{session_key_prefix}_filters_form_{st.session_state[form_key]}"):
                filters: Dict[str, Any] = {}
                col_n, col_candidate_type = st.columns(2)
                with col_n:
                    filters["n"] = st.selectbox(
                        "Grid Size (N)",
                        options=[None, 4, 9],
                        format_func=lambda x: str(x) if x else "All",
                        index=0
                    )

                with col_candidate_type:
                    filters["candidate_type"] = st.selectbox(
                        "Candidate Type",
                        options=[None] + [x.value for x in SudokuSimplifiedCandidateType],
                        format_func=lambda x: SudokuSimplifiedCandidateType(x).display_name if x is not None else "All",
                        index=0
                    )

                col_clear, col_apply = st.columns([1, 3])
                with col_clear:
                    clear_clicked = st.form_submit_button("Clear 🔃", use_container_width=True)
                with col_apply:
                    apply_clicked = st.form_submit_button("Apply ✅", use_container_width=True)

            if clear_clicked:
                st.session_state[form_key] += 1
                st.session_state[filters_key] = {}
                st.rerun()

            if apply_clicked:
                st.session_state[filters_key] = filters
                st.rerun()

        return st.session_state[filters_key]
