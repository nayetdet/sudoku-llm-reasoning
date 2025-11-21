import streamlit as st

from webui.components.galleries.sudoku_image_gallery_component import SudokuImageGalleryComponent
from webui.components.tables.sudoku_inference_analytics_table_component import SudokuInferenceAnalyticsTableComponent
from webui.components.tables.sudoku_table_component import SudokuTableComponent

tabs = st.tabs(["Galeria de Imagens", "Análises de Inferência", "Tabela de Sudokus"])

with tabs[0]:
    SudokuImageGalleryComponent.render()

with tabs[1]:
    SudokuInferenceAnalyticsTableComponent.render()

with tabs[2]:
    SudokuTableComponent.render()
