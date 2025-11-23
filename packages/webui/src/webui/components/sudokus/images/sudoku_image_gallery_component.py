import streamlit as st
from typing import List, Dict, Any
from webui.components.shared.pagination_component import PaginationComponent
from webui.components.sudokus.filters.sudoku_filter_component import SudokuFilterComponent
from webui.schemas.sudoku_image_schema import SudokuImageSchema
from webui.schemas.sudoku_schema import SudokuSchema
from webui.services.sudoku_image_service import SudokuImageService
from webui.services.sudoku_service import SudokuService
from webui.components.shared.image_component import ImageComponent, Image

class SudokuImageGalleryComponent:
    @classmethod
    def render(cls) -> None:
        st.session_state.setdefault("sudoku_image_gallery_page", 0)
        sudoku_filters: Dict[str, Any] = SudokuFilterComponent.render(session_key_prefix="sudoku_image_gallery", filters={"n", "candidate_type"})
        total_sudokus, sudokus = SudokuService.get_all(page=st.session_state.sudoku_image_gallery_page, size=1, **sudoku_filters)
        if not sudokus:
            st.info("No sudokus found.")
            return

        sudoku: SudokuSchema = sudokus[0]
        st.markdown(f"### Sudoku #{sudoku.id} — {sudoku.n}x{sudoku.n} | {sudoku.candidate_type.display_name}")
        images: List[SudokuImageSchema] = SudokuImageService.get_all_pages(sudoku.id)
        if not images:
            st.warning("No images for this sudokus.")
            return

        ImageComponent.render(
            images=[
                Image(content_base64=image.content_base64, mime=image.mime)
                for image in images
            ],
            height=500
        )

        st.divider()
        PaginationComponent.render(
            session_key_prefix="sudoku_image_gallery",
            label="Sudoku",
            total_elements=total_sudokus
        )
