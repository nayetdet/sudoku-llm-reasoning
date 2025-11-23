import streamlit as st
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable

@dataclass(frozen=True)
class Filter:
    key: str
    label: str
    options: List[Any]
    format_func: Callable[[Any], str] = str
    index: Optional[int] = 0

class FilterComponent:
    @classmethod
    def render(cls, session_key_prefix: str, filters: List[Filter], cols_per_row: int = 2) -> Dict[str, Any]:
        form_key: str = f"{session_key_prefix}_filters_form_key"
        filters_key: str = f"{session_key_prefix}_filters"

        st.session_state.setdefault(form_key, 0)
        st.session_state.setdefault(filters_key, {})
        with st.expander("Filters"):
            with st.form(f"{session_key_prefix}_filters_form_{st.session_state[form_key]}"):
                applied_filters: Dict[str, Any] = {}
                for i in range(0, len(filters), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for col, current_filter in zip(cols, filters[i : i + cols_per_row]):
                        with col:
                            applied_filters[current_filter.key] = st.selectbox(
                                label=current_filter.label,
                                options=current_filter.options,
                                format_func=current_filter.format_func,
                                index=current_filter.index
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
                st.session_state[filters_key] = applied_filters
                st.rerun()

        return st.session_state[filters_key]
