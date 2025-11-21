import html
from typing import Dict

import streamlit.components.v1 as components


class SudokuImageComponent:
    @staticmethod
    def render(image: Dict[str, str]) -> None:
        image_src: str = html.escape(image["src"])
        viewer_html: str = """
<style>
  .sudoku-viewer {
    position: relative;
    width: 100%;
    height: clamp(320px, 70vh, 900px);
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #444;
    background: radial-gradient(circle at 25% 20%, #1b2330, #0f1115 55%);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
  }

  .sudoku-viewer__surface {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: grab;
    background: linear-gradient(145deg, rgba(255, 255, 255, 0.03), rgba(255, 255, 255, 0));
  }

  .sudoku-viewer__img {
    max-width: 100%;
    max-height: 100%;
    width: auto;
    height: auto;
    object-fit: contain;
    user-select: none;
    pointer-events: none;
    transform: translate(0px, 0px) scale(1);
    transition: transform 120ms ease-out;
    will-change: transform;
  }

  @media (max-width: 900px) {
    .sudoku-viewer {
      height: clamp(260px, 60vh, 680px);
    }
  }
</style>

<div class="sudoku-viewer">
  <div class="sudoku-viewer__surface" id="sudoku-viewer-surface">
    <img class="sudoku-viewer__img" id="sudoku-viewer-img" src="__SRC__" alt="Sudoku image" draggable="false" />
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
  const minScale = 0.5;
  const maxScale = 6;

  const updateTransform = () => {
    img.style.transform = `translate(${originX}px, ${originY}px) scale(${scale})`;
  };

  const resetPosition = () => {
    scale = 1;
    originX = 0;
    originY = 0;
    updateTransform();
  };

  surface.addEventListener('wheel', (event) => {
    event.preventDefault();
    const direction = event.deltaY < 0 ? 1 : -1;
    const step = scale * 0.1;
    scale = Math.min(maxScale, Math.max(minScale, scale + direction * step));
    updateTransform();
  }, { passive: false });

  surface.addEventListener('mousedown', (event) => {
    isPanning = true;
    startX = event.clientX - originX;
    startY = event.clientY - originY;
    surface.style.cursor = 'grabbing';
  });

  window.addEventListener('mouseup', () => {
    if (!isPanning) return;
    isPanning = false;
    surface.style.cursor = 'grab';
  });

  window.addEventListener('mousemove', (event) => {
    if (!isPanning) return;
    originX = event.clientX - startX;
    originY = event.clientY - startY;
    updateTransform();
  });

  surface.addEventListener('dblclick', resetPosition);
  window.addEventListener('resize', resetPosition);

  resetPosition();
})();
</script>
"""

        components.html(viewer_html.replace("__SRC__", image_src), height=860)
