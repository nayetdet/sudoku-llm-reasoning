import streamlit as st
from webui.components.sudoku.images.sudoku_image_gallery_component import SudokuImageGalleryComponent
from webui.components.sudoku.tables.sudoku_inference_analytics_table_component import SudokuInferenceAnalyticsTableComponent
from webui.components.sudoku.tables.sudoku_table_component import SudokuTableComponent

st.set_page_config(page_title="Sudoku LLM Reasoning")
st.title("Sudoku LLM Reasoning: WebUI")
gallery_tab, analytics_tab, sudoku_tab = st.tabs(["Image Gallery", "Inference Analytics", "Sudoku Table"])

with gallery_tab:
    SudokuImageGalleryComponent.render()

with analytics_tab:
    SudokuInferenceAnalyticsTableComponent.render()

with sudoku_tab:
    SudokuTableComponent.render()
