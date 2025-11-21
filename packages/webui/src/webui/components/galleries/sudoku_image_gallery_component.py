import html
from typing import Dict, List, Tuple
import streamlit as st
import streamlit.components.v1 as components
from core.enums.sudoku_simplified_candidate_type import SudokuSimplifiedCandidateType
from webui.schemas.sudoku_schema import SudokuSchema
from webui.services.sudoku_service import SudokuService

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

        total_sudokus, sudokus = cls.__load_sudokus()
        images: List[Dict[str, str]] = cls.__flatten_images(sudokus)

        if not images:
            st.info("Nenhuma imagem encontrada com os filtros atuais. Ajuste os filtros ou navegue para outras páginas.")
            cls.__render_page_navigation(total_sudokus)
            return

        if st.session_state.gallery_image_index >= len(images):
            st.session_state.gallery_image_index = max(len(images) - 1, 0)

        cls.__render_image_navigation(len(images))
        cls.__render_viewer(images[st.session_state.gallery_image_index])
        cls.__render_page_navigation(total_sudokus)

    @classmethod
    def __render_filters(cls) -> None:
        with st.expander("Filtros", expanded=True):
            with st.form("gallery_filters_form"):
                n_raw: str = st.text_input(
                    "Filtrar por N",
                    value=str(st.session_state.gallery_filters.get("n") or ""),
                    placeholder="Ex.: 9"
                )

                candidate_options: List = [None] + list(SudokuSimplifiedCandidateType)
                current_candidate_value: str = st.session_state.gallery_filters.get("candidate_type")
                default_candidate = next(
                    (opt for opt in candidate_options if (opt and opt.value == current_candidate_value) or (opt is None and current_candidate_value is None)),
                    None
                )

                candidate = st.selectbox(
                    "Candidate Type",
                    options=candidate_options,
                    format_func=lambda opt: opt.display_name if isinstance(opt, SudokuSimplifiedCandidateType) else "Todos",
                    index=candidate_options.index(default_candidate) if default_candidate in candidate_options else 0
                )

                submitted: bool = st.form_submit_button("Aplicar filtros")

            if submitted:
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
    def __load_sudokus(cls) -> Tuple[int, List[SudokuSchema]]:
        filters: Dict[str, object] = {
            "page": st.session_state.gallery_page,
            "size": cls.PAGE_SIZE
        }

        if st.session_state.gallery_filters.get("n") is not None:
            filters["n"] = st.session_state.gallery_filters["n"]

        if st.session_state.gallery_filters.get("candidate_type"):
            filters["candidate_type"] = st.session_state.gallery_filters["candidate_type"]

        return SudokuService.get_all(**filters)

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
    def __render_page_navigation(cls, total_sudokus: int) -> None:
        total_pages: int = (total_sudokus + cls.PAGE_SIZE - 1) // cls.PAGE_SIZE
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
            st.write(f"Sudoku ID: {image['sudoku_id']} | N: {image['n']} | Candidate: {image['candidate_type']} | Imagem {image['position']}")

        image_src: str = html.escape(image["src"])
        viewer_html: str = """
            <div id="sudoku-viewer" style="position: relative; width: 100%; height: 70vh; border-radius: 12px; overflow: hidden; border: 1px solid #444; background: radial-gradient(circle at 25% 20%, #1b2330, #0f1115 55%);">
              <div id="sudoku-viewer-surface" style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; cursor: grab;">
                <img id="sudoku-viewer-img" src="__SRC__" alt="Sudoku image" style="max-width: none; max-height: none; user-select: none; pointer-events: none; transform: translate(0px, 0px) scale(1);" draggable="false" />
              </div>
            </div>
            <script>
            (function() {
              const surface = document.getElementById('sudoku-viewer-surface');
              const img = document.getElementById('sudoku-viewer-img');
              let scale = 1;
              let originX = 0;
              let originY = 0;
              let isPanning = false;
              let startX = 0;
              let startY = 0;
              const minScale = 0.4;
              const maxScale = 6;
            
              const updateTransform = () => {
                img.style.transform = `translate(${originX}px, ${originY}px) scale(${scale})`;
              };
            
              surface.addEventListener('wheel', (event) => {
                event.preventDefault();
                const delta = event.deltaY < 0 ? 0.1 : -0.1;
                scale = Math.min(maxScale, Math.max(minScale, scale + delta));
                updateTransform();
              });
            
              surface.addEventListener('mousedown', (event) => {
                isPanning = true;
                startX = event.clientX - originX;
                startY = event.clientY - originY;
                surface.style.cursor = 'grabbing';
              });
            
              window.addEventListener('mouseup', () => {
                isPanning = false;
                surface.style.cursor = 'grab';
              });
            
              window.addEventListener('mousemove', (event) => {
                if (!isPanning) return;
                originX = event.clientX - startX;
                originY = event.clientY - startY;
                updateTransform();
              });
            
              surface.addEventListener('dblclick', () => {
                scale = 1;
                originX = 0;
                originY = 0;
                updateTransform();
              });
            
              updateTransform();
            })();
            </script>
            """

        components.html(viewer_html.replace("__SRC__", image_src), height=720)
