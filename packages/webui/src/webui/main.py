import textwrap

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
    st.markdown(
        textwrap.dedent("""
        ### 🧩 Explicação dos campos e grupos de inferência
        Cada Sudoku inferido pela LLM possui quatro campos principais:
        
        - **`succeeded`**: indica que a LLM encontrou **um dos Single Candidates previstos** pelo nosso código.  
        - **`succeeded_nth_layer`**: indica que a LLM encontrou **um candidato que torna o Sudoku válido**.  
        - **`succeeded_and_unique_nth_layer`**: indica que a LLM encontrou **um candidato que torna o Sudoku válido *e* é um Single Candidate**.  
        - **`explanation`**: texto explicativo retornado pela LLM ao justificar o candidato encontrado.
        
        A partir desses quatro campos, as inferências são classificadas em **seis grupos mutuamente exclusivos**:
        | Grupo | Condições | Significado |
        |:--|:--|:--|
        | **Predicted** | `succeeded=True`, `succeeded_nth_layer=True` | A LLM encontrou um *Single Candidate* previsto pelo nosso código (correspondência direta). |
        | **Beyond** | `succeeded=False`, `succeeded_nth_layer=True`, `succeeded_and_unique_nth_layer=True` | A LLM encontrou um *Single Candidate* válido que **não estava previsto** pelo nosso código — ou seja, foi além do planejado. |
        | **Beyond (Non-unique)** | `succeeded=False`, `succeeded_nth_layer=True`, `succeeded_and_unique_nth_layer=False` | A LLM encontrou um candidato que **torna o Sudoku válido**, mas **não é um Single Candidate**. |
        | **Hallucination** | `succeeded=False`, `succeeded_nth_layer=False`, `explanation≠None` | A LLM propôs um candidato que **não torna o Sudoku válido** — é uma **alucinação**. |
        | **Missed** | `succeeded=False`, `succeeded_nth_layer=False`, `explanation=None` | A LLM **não tentou nenhuma inferência** (não gerou explicação). |
        | **Unprocessed** | Inferência inexistente | Sudoku **ainda não processado** pela LLM. |
        """)
    )

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
