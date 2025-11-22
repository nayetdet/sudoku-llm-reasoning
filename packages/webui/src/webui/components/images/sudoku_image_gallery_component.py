import streamlit as st
from typing import List, Dict, Any
from core.enums.sudoku_simplified_candidate_type import SudokuSimplifiedCandidateType
from webui.schemas.sudoku_image_schema import SudokuImageSchema
from webui.schemas.sudoku_schema import SudokuSchema
from webui.services.sudoku_image_service import SudokuImageService
from webui.services.sudoku_service import SudokuService
from webui.components.images.image_component import ImageComponent, Image

class SudokuImageGalleryComponent:
    @classmethod
    def render(cls) -> None:
        st.session_state.setdefault("sudoku_image_gallery_page", 0)
        st.session_state.setdefault("sudoku_image_gallery_filters_form_key", 0)
        st.session_state.setdefault("sudoku_image_gallery_filters", {})

        st.title("🖼️ Sudoku Image Gallery")
        with st.expander("Filters", expanded=True):
            with st.form(f"sudoku_image_gallery_filters_form_{st.session_state.sudoku_image_gallery_filters_form_key}"):
                filters: Dict[str, Any] = {}
                col_n, col_candidate_type = st.columns(2)
                with col_n:
                    filters["n"] = st.selectbox(
                        label="Grid Size (N)",
                        options=[None, 4, 9],
                        format_func=lambda x: str(x) if x else "All",
                        index=0
                    )

                with col_candidate_type:
                    filters["candidate_type"] = st.selectbox(
                        label="Candidate Type",
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
                st.session_state.sudoku_image_gallery_page = 0
                st.session_state.sudoku_image_gallery_filters_form_key += 1
                st.session_state.sudoku_image_gallery_filters = {}
                st.rerun()

            if apply_clicked:
                st.session_state.sudoku_image_gallery_page = 0
                st.session_state.sudoku_image_gallery_filters = filters
                st.rerun()

        total_sudokus, sudokus = SudokuService.get_all(page=st.session_state.sudoku_image_gallery_page, size=1, **st.session_state.sudoku_image_gallery_filters)
        if not sudokus:
            st.info("No sudokus found.")
            return

        sudoku: SudokuSchema = sudokus[0]
        st.markdown(f"### Sudoku #{sudoku.id} — {sudoku.n}x{sudoku.n} | {sudoku.candidate_type.display_name}")
        images: List[SudokuImageSchema] = SudokuImageService.get_all_pages(sudoku.id)
        if not images:
            st.warning("No images for this sudoku.")
            return

        ImageComponent.render(images=[Image(content_base64=image.content_base64, mime=image.mime) for image in images], height=500)
        st.divider()

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
