import streamlit as st
from webui.components.sudokus.charts.sudoku_inference_analytics_chart_component import SudokuInferenceAnalyticsChartComponent
from webui.components.sudokus.images.sudoku_image_gallery_component import SudokuImageGalleryComponent
from webui.components.sudokus.tables.sudoku_inference_analytics_table_component import SudokuInferenceAnalyticsTableComponent
from webui.components.sudokus.tables.sudoku_table_component import SudokuTableComponent

st.set_page_config(page_title="Sudoku LLM Reasoning")
st.title("Sudoku LLM Reasoning: WebUI")

gallery_tab, analytics_tab, sudoku_tab = st.tabs(["Image Gallery", "Inference Analytics", "Sudoku"])
with gallery_tab:
    st.title("🖼️ Sudoku Image Gallery")
    st.divider()
    SudokuImageGalleryComponent.render()

with analytics_tab:
    st.title("📊 Sudoku Inference Analytics")
    st.divider()
    st.subheader("📋 Summary Table")
    SudokuInferenceAnalyticsTableComponent.render()

    st.divider()
    st.subheader("📈 Comparative Chart")
    SudokuInferenceAnalyticsChartComponent.render()

with sudoku_tab:
    st.title("📊 Sudoku")
    st.divider()
    st.subheader("📋 Summary Table")
    SudokuTableComponent.render()
