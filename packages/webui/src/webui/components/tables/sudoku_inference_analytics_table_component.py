import pandas as pd
import streamlit as st
from typing import List, Dict, Any
from webui.schemas.sudoku_inference_analysis_schema import SudokuInferenceAnalyticsSchema
from webui.services.sudoku_inference_service import SudokuInferenceService

class SudokuInferenceAnalyticsTableComponent:
    @classmethod
    def render(cls) -> None:
        analytics: List[SudokuInferenceAnalyticsSchema] = SudokuInferenceService.get_analytics()
        if not analytics:
            st.info("No analytics found.")
            return

        df: pd.DataFrame = cls.__get_dataframe(analytics)
        st.title("📊 Sudoku Inference Analytics")
        filtered_df: pd.DataFrame = cls.__filter_dataframe(df)
        st.dataframe(filtered_df, hide_index=True, width="stretch")

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

    @classmethod
    def __filter_dataframe(cls, df: pd.DataFrame) -> pd.DataFrame:
        candidate_types = sorted(df["Candidate Type"].unique())
        selected_types = st.multiselect(
            "Filtrar por tipo de candidato",
            candidate_types,
            default=candidate_types,
            key="analytics_candidate_filter",
        )
        if selected_types:
            return df[df["Candidate Type"].isin(selected_types)]
        return df
