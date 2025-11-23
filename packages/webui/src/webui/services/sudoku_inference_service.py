import streamlit as st
import requests
from typing import List
from webui.config import Config
from webui.schemas.sudoku_inference_analysis_schema import SudokuInferenceAnalyticsSchema

class SudokuInferenceService:
    @classmethod
    @st.cache_data(show_spinner=False)
    def get_analytics(cls) -> List[SudokuInferenceAnalyticsSchema]:
        response: requests.Response = requests.get(url=f"{Config.WebUI.API_URL}/v1/sudokus/inferences/analytics")
        response.raise_for_status()
        return [SudokuInferenceAnalyticsSchema.model_validate(x) for x in response.json()]
