import textwrap
import streamlit.components.v1 as components
from typing import List, Optional
from webui.schemas.sudoku_image_schema import SudokuImageSchema

class SudokuImageComponent:
    @classmethod
    def render(cls, images: List[SudokuImageSchema], height: Optional[int] = None) -> None:
        if not images:
            return

        js_images: str = f"""[{", ".join(f"{{ src: 'data:{image.mime};base64,{image.content_base64}' }}" for image in images)}]"""
        html_content = textwrap.dedent(f"""
            <style>
                html, body {{
                    margin: 0;
                    padding: 0;
                    overflow: hidden;
                    width: 100%;
                    height: 100%;
                }}

                .image-viewer {{
                    position: relative;
                    width: 100%;
                    height: 100%;
                    border-radius: 12px;
                    overflow: hidden;
                    border: 1px solid #333;
                    background: radial-gradient(circle at 25% 20%, #1a1f29, #0e1013 60%);
                    box-shadow: 0 8px 28px rgba(0,0,0,0.4);
                }}

                .image-viewer__surface {{
                    width: 100%;
                    height: 100%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: grab;
                    background-color: #0e1013;
                    overflow: hidden;
                }}

                .image-viewer__img {{
                    max-width: 100%;
                    max-height: 100%;
                    object-fit: contain;
                    user-select: none;
                    pointer-events: auto;
                    transition: transform 100ms ease-out;
                    will-change: transform;
                }}

                .image-viewer__nav {{
                    position: absolute;
                    top: 50%;
                    transform: translateY(-50%);
                    width: 48px;
                    height: 48px;
                    background: rgba(0,0,0,0.4);
                    border: none;
                    border-radius: 50%;
                    color: white;
                    font-size: 22px;
                    cursor: pointer;
                    opacity: 0.6;
                    transition: opacity 0.2s ease, background 0.2s ease;
                    z-index: 10;
                }}

                .image-viewer__nav:hover {{
                    opacity: 1;
                    background: rgba(0,0,0,0.6);
                }}

                .image-viewer__nav--left {{ 
                    left: 12px;
                }}

                .image-viewer__nav--right {{
                    right: 12px;
                }}

                .image-viewer__indicator {{
                    position: absolute;
                    bottom: 10px;
                    left: 50%;
                    transform: translateX(-50%);
                    color: #ccc;
                    font-family: monospace;
                    font-size: 13px;
                    background: rgba(0, 0, 0, 0.35);
                    padding: 4px 10px;
                    border-radius: 8px;
                }}
            </style>

            <div class="image-viewer" id="viewer">
                <div class="image-viewer__surface" id="surface">
                    <img id="img" class="image-viewer__img" src="" draggable="false"/>
                </div>

                <button class="image-viewer__nav image-viewer__nav--left" id="btn-prev">⟨</button>
                <button class="image-viewer__nav image-viewer__nav--right" id="btn-next">⟩</button>
                <div class="image-viewer__indicator" id="indicator">1 / 1</div>
            </div>

            <script>
            (() => {{
                const images = {js_images};
                const img = document.getElementById("img");
                const surface = document.getElementById("surface");
                const indicator = document.getElementById("indicator");

                let current = 0;
                let scale = 1, originX = 0, originY = 0;
                let isPanning = false, startX = 0, startY = 0;
                const MIN_SCALE = 0.5, MAX_SCALE = 6;

                const updateTransform = () => {{
                    img.style.transform = `translate(${{originX}}px, ${{originY}}px) scale(${{scale}})`;
                }};

                const resetView = () => {{
                    scale = 1;
                    originX = originY = 0;
                    updateTransform();
                }};

                const loadImage = (index) => {{
                    img.src = images[index].src;
                    indicator.textContent = `${{index + 1}} / ${{images.length}}`;
                    resetView();
                }};

                surface.addEventListener("wheel", (e) => {{
                    e.preventDefault();
                    const rect = surface.getBoundingClientRect();
                    const offsetX = e.clientX - rect.left - rect.width / 2;
                    const offsetY = e.clientY - rect.top - rect.height / 2;
                    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
                    const newScale = Math.min(MAX_SCALE, Math.max(MIN_SCALE, scale * zoomFactor));
                    originX -= offsetX * (newScale / scale - 1);
                    originY -= offsetY * (newScale / scale - 1);
                    scale = newScale;
                    updateTransform();
                }}, {{ passive: false }});

                surface.addEventListener("mousedown", (e) => {{
                    if (e.button !== 0) return;
                    isPanning = true;
                    startX = e.clientX - originX;
                    startY = e.clientY - originY;
                    surface.style.cursor = "grabbing";
                }});

                window.addEventListener("mouseup", () => {{
                    isPanning = false;
                    surface.style.cursor = "grab";
                }});

                window.addEventListener("mousemove", (e) => {{
                    if (!isPanning) return;
                    originX = e.clientX - startX;
                    originY = e.clientY - startY;
                    updateTransform();
                }});

                surface.addEventListener("dblclick", resetView);
                document.getElementById("btn-prev").onclick = () => {{
                    current = (current - 1 + images.length) % images.length;
                    loadImage(current);
                }};

                document.getElementById("btn-next").onclick = () => {{
                    current = (current + 1) % images.length;
                    loadImage(current);
                }};

                loadImage(current);
            }})();
            </script>
        """)

        components.html(html_content, height=height, scrolling=False)
