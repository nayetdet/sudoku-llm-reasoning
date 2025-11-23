import streamlit as st

class PaginationComponent:
    @classmethod
    def render(cls, session_key_prefix: str, label: str, total_elements: int) -> int:
        page_key: str = f"{session_key_prefix}_page"
        st.session_state.setdefault(page_key, 0)

        current_page: int = st.session_state[page_key]
        col_previous, col_next = st.columns(2)
        with col_previous:
            if st.button("⬅ Previous", use_container_width=True, key=f"{session_key_prefix}_prev_btn"):
                st.session_state[page_key] = (current_page - 1) % total_elements
                st.rerun()

        with col_next:
            if st.button("Next ➡", use_container_width=True, key=f"{session_key_prefix}_next_btn"):
                st.session_state[page_key] = (current_page + 1) % total_elements
                st.rerun()

        st.caption(f"{label} {current_page + 1} of {total_elements}")
        return st.session_state[page_key]
