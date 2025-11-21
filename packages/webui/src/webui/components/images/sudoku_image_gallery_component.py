from typing import Dict, List, Tuple
import streamlit as st
from core.enums.sudoku_simplified_candidate_type import SudokuSimplifiedCandidateType
from webui.schemas.sudoku_schema import SudokuSchema
from webui.services.sudoku_service import SudokuService
from webui.components.images.sudoku_image_component import SudokuImageComponent

class SudokuImageGalleryComponent:
    PAGE_SIZE: int = 6

    @classmethod
    def render(cls) -> None:
        if "gallery_filters" not in st.session_state:
            st.session_state.gallery_filters = {"n": None, "candidate_type": None}

        if "gallery_page" not in st.session_state:
            st.session_state.gallery_page = 0

        if "gallery_image_index" not in st.session_state:
            st.session_state.gallery_image_index = 0

        st.title("🖼️ Sudoku Image Gallery")
        st.caption("Use o scroll para dar zoom, arraste para mover e dê duplo clique para resetar a posição.")

        cls.__render_filters()

        total_sudokus, sudokus, page_size = cls.__load_sudokus()
        images: List[Dict[str, str]] = cls.__flatten_images(sudokus)

        if not images:
            st.info("Nenhuma imagem encontrada com os filtros atuais. Ajuste os filtros ou navegue para outras páginas.")
            cls.__render_page_navigation(total_sudokus, page_size)
            return

        if st.session_state.gallery_image_index >= len(images):
            st.session_state.gallery_image_index = max(len(images) - 1, 0)

        cls.__render_image_navigation(len(images))
        cls.__render_viewer(images[st.session_state.gallery_image_index])
        cls.__render_page_navigation(total_sudokus, page_size)

    @classmethod
    def __render_filters(cls) -> None:
        with st.expander("Filtros", expanded=True):
            with st.form("gallery_filters_form"):
                filters_cols = st.columns([1, 1])

                with filters_cols[0]:
                    n_raw: str = st.text_input(
                        "Filtrar por N",
                        value=str(st.session_state.gallery_filters.get("n") or ""),
                        placeholder="Ex.: 9",
                        help="Use um inteiro positivo para buscar um tamanho específico."
                    )

                candidate_options: List = [None] + list(SudokuSimplifiedCandidateType)
                current_candidate_value: str = st.session_state.gallery_filters.get("candidate_type")
                default_candidate = next(
                    (opt for opt in candidate_options if (opt and opt.value == current_candidate_value) or (opt is None and current_candidate_value is None)),
                    None
                )

                with filters_cols[1]:
                    candidate = st.selectbox(
                        "Tipo de candidato",
                        options=candidate_options,
                        format_func=lambda opt: opt.display_name if isinstance(opt, SudokuSimplifiedCandidateType) else "Todos",
                        index=candidate_options.index(default_candidate) if default_candidate in candidate_options else 0,
                        help="Filtra pelos tipos simplificados de candidatos disponíveis."
                    )

                button_cols = st.columns([1, 1])
                apply_filters: bool = button_cols[0].form_submit_button("Aplicar filtros", use_container_width=True)
                clear_filters: bool = button_cols[1].form_submit_button("Limpar", use_container_width=True, type="secondary")

            if clear_filters:
                st.session_state.gallery_filters = {"n": None, "candidate_type": None}
                st.session_state.gallery_page = 0
                st.session_state.gallery_image_index = 0
                st.rerun()

            if apply_filters:
                n_value = None
                if n_raw.strip():
                    try:
                        n_value = int(n_raw.strip())
                        if n_value <= 0:
                            raise ValueError()
                    except ValueError:
                        st.error("N precisa ser um inteiro positivo.")
                        return

                st.session_state.gallery_filters = {
                    "n": n_value,
                    "candidate_type": candidate.value if candidate else None
                }
                st.session_state.gallery_page = 0
                st.session_state.gallery_image_index = 0
                st.rerun()

    @classmethod
    def __load_sudokus(cls) -> Tuple[int, List[SudokuSchema], int]:
        filters: Dict[str, object] = {
            "page": st.session_state.gallery_page,
            "size": cls.PAGE_SIZE
        }

        if st.session_state.gallery_filters.get("n") is not None:
            filters["n"] = st.session_state.gallery_filters["n"]

        if st.session_state.gallery_filters.get("candidate_type"):
            filters["candidate_type"] = st.session_state.gallery_filters["candidate_type"]

        total_sudokus, sudokus = SudokuService.get_all(**filters)
        page_size_used: int = filters["size"]

        total_pages: int = max((total_sudokus + page_size_used - 1) // page_size_used, 1)
        if st.session_state.gallery_page >= total_pages:
            st.session_state.gallery_page = total_pages - 1
            filters["page"] = st.session_state.gallery_page
            total_sudokus, sudokus = SudokuService.get_all(**filters)

        return total_sudokus, sudokus, page_size_used

    @classmethod
    def __flatten_images(cls, sudokus: List[SudokuSchema]) -> List[Dict[str, str]]:
        images: List[Dict[str, str]] = []
        for sudoku in sudokus:
            for idx, image in enumerate(sudoku.images):
                if not image.content_base64:
                    continue

                images.append({
                    "src": f"data:{image.mime};base64,{image.content_base64}",
                    "sudoku_id": str(sudoku.id),
                    "n": str(sudoku.n),
                    "candidate_type": sudoku.candidate_type.display_name,
                    "position": f"{idx + 1} / {len(sudoku.images)}"
                })

        return images

    @classmethod
    def __render_image_navigation(cls, total_images: int) -> None:
        left_col, center_col, right_col = st.columns([1, 2, 1])

        with left_col:
            if st.button("⬅️ Imagem anterior", disabled=st.session_state.gallery_image_index <= 0, use_container_width=True):
                st.session_state.gallery_image_index -= 1
                st.rerun()

        with center_col:
            st.markdown(
                f"<div style='text-align:center; padding: 8px 0;'><strong>Imagem {st.session_state.gallery_image_index + 1} de {total_images}</strong></div>",
                unsafe_allow_html=True
            )

        with right_col:
            if st.button("Próxima imagem ➡️", disabled=st.session_state.gallery_image_index + 1 >= total_images, use_container_width=True):
                st.session_state.gallery_image_index += 1
                st.rerun()

    @classmethod
    def __render_page_navigation(cls, total_sudokus: int, page_size: int) -> None:
        total_pages: int = (total_sudokus + page_size - 1) // page_size
        if total_pages == 0:
            total_pages = 1

        left_col, center_col, right_col = st.columns([1, 2, 1])

        with left_col:
            if st.button("⬅️ Página anterior", disabled=st.session_state.gallery_page == 0, use_container_width=True):
                st.session_state.gallery_page = max(st.session_state.gallery_page - 1, 0)
                st.session_state.gallery_image_index = 0
                st.rerun()

        with center_col:
            st.markdown(
                f"<div style='text-align:center; padding: 8px 0;'><strong>Página {st.session_state.gallery_page + 1} de {total_pages}</strong></div>",
                unsafe_allow_html=True
            )

        with right_col:
            if st.button("Próxima página ➡️", disabled=st.session_state.gallery_page + 1 >= total_pages, use_container_width=True):
                st.session_state.gallery_page += 1
                st.session_state.gallery_image_index = 0
                st.rerun()

    @classmethod
    def __render_viewer(cls, image: Dict[str, str]) -> None:
        metadata_col, _ = st.columns([3, 2])
        with metadata_col:
            st.write(f"Sudoku ID: {image['sudoku_id']} | N: {image['n']} | Tipo de candidato: {image['candidate_type']} | Imagem {image['position']}")

        SudokuImageComponent.render(image)
