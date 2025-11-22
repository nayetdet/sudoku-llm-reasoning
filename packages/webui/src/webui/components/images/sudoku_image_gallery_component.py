import streamlit as st
from typing import List, Dict, Any, Optional
from core.enums.sudoku_simplified_candidate_type import SudokuSimplifiedCandidateType
from webui.schemas.sudoku_image_schema import SudokuImageSchema
from webui.schemas.sudoku_schema import SudokuSchema
from webui.services.sudoku_image_service import SudokuImageService
from webui.services.sudoku_service import SudokuService
from webui.components.images.sudoku_image_component import SudokuImageComponent

class SudokuImageGalleryComponent:
    @classmethod
    def render(cls) -> None:
        if "sudoku_image_gallery_page" not in st.session_state:
            st.session_state.sudoku_image_gallery_page = 0
        if "sudoku_image_gallery_filters" not in st.session_state:
            st.session_state.sudoku_image_gallery_filters = {}

        st.title("🖼️ Sudoku Image Gallery")
        with st.expander("Filters", expanded=True):
            with st.form("sudoku_image_gallery_filters_form"):
                filters: Dict[str, Any] = st.session_state.sudoku_image_gallery_filters.copy()
                col_n, col_candidate_type = st.columns(2)
                with col_n:
                    filters["n"] = st.selectbox(
                        label="Grid Size (N)",
                        options=[None, 4, 9],
                        format_func=lambda x: str(x) if x else "All"
                    )

                with col_candidate_type:
                    filters["candidate_type"] = st.selectbox(
                        label="Candidate Type",
                        options=[None] + list(SudokuSimplifiedCandidateType),
                        format_func=lambda x: x.display_name if isinstance(x, SudokuSimplifiedCandidateType) else "All"
                    )

                    if isinstance(filters["candidate_type"], SudokuSimplifiedCandidateType):
                        filters["candidate_type"] = filters["candidate_type"].value

                col_clear, col_apply = st.columns([1, 3])
                with col_clear:
                    clear_clicked = st.form_submit_button("Clear 🔃", use_container_width=True)

                with col_apply:
                    apply_clicked = st.form_submit_button("Apply ✅", use_container_width=True)

            if apply_clicked:
                st.session_state.sudoku_image_gallery_filters = filters

            if clear_clicked:
                st.session_state.sudoku_image_gallery_filters = {}
                st.rerun()

        total_sudokus, sudokus = SudokuService.get_all(page=st.session_state.sudoku_image_gallery_page, size=1, **filters)
        if not sudokus:
            st.info("No sudokus found.")
            return

        sudoku: SudokuSchema = sudokus[0]
        st.markdown(f"### Sudoku #{sudoku.id} — {sudoku.n}x{sudoku.n} | {sudoku.candidate_type.display_name}")
        images: List[SudokuImageSchema] = SudokuImageService.get_all_pages(sudoku.id)
        if not images:
            st.warning("No images for this sudoku.")
            return

        SudokuImageComponent.render(images, height=800)
        col_previous, col_next = st.columns(2)
        with col_previous:
            if st.button("⬅ Previous Sudoku", use_container_width=True):
                st.session_state.sudoku_image_gallery_page = ((st.session_state.sudoku_image_gallery_page - 1) % total_sudokus)
                st.rerun()

        with col_next:
            if st.button("Next Sudoku ➡", use_container_width=True):
                st.session_state.sudoku_image_gallery_page = ((st.session_state.sudoku_image_gallery_page + 1) % total_sudokus)
                st.rerun()

        st.caption(f"Sudoku {st.session_state.sudoku_image_gallery_page + 1} of {total_sudokus}")
