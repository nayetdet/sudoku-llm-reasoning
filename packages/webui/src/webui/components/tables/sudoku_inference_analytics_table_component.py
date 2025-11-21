import pandas as pd
import streamlit as st
from typing import List, Dict, Any
from webui.schemas.sudoku_inference_analysis_schema import SudokuInferenceAnalyticsSchema
from webui.services.sudoku_inference_service import SudokuInferenceService

class SudokuInferenceAnalyticsTableComponent:
    @classmethod
    def render(cls) -> None:
        analytics: List[SudokuInferenceAnalyticsSchema] = SudokuInferenceService.get_analytics()
        df: pd.DataFrame = cls.__get_dataframe(analytics)

        st.title("📊 Sudoku Analysis Table")
        st.dataframe(df, hide_index=True, use_container_width=True)

    @classmethod
    def __get_dataframe(cls, analytics: List[SudokuInferenceAnalyticsSchema]) -> pd.DataFrame:
        rows: List[Dict[str, Any]] = []
        for analytic in analytics:
            total: int = analytic.total if analytic.total > 0 else 1
            rows.append({
                "N": analytic.n,
                "Candidate Type": analytic.candidate_type.display_name,
                "Planned (%)": f"{(analytic.total_planned / total) * 100:.2f}%",
                "Beyond (%)": f"{(analytic.total_beyond / total) * 100:.2f}%",
                "Hallucinations (%)": f"{(analytic.total_hallucinations / total) * 100:.2f}%",
                "Missed (%)": f"{(analytic.total_missed / total) * 100:.2f}%",
                "Unprocessed (%)": f"{(analytic.total_unprocessed / total) * 100:.2f}%",
                "Total": analytic.total
            })
        return pd.DataFrame(rows)
