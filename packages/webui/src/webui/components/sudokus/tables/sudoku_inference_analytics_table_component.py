import pandas as pd
import streamlit as st
from typing import List, Dict, Any
from core.enums.sudoku_simplified_candidate_type import SudokuSimplifiedCandidateType
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
        st.dataframe(df, hide_index=True, width="stretch")

    @classmethod
    def __get_dataframe(cls, analytics: List[SudokuInferenceAnalyticsSchema]) -> pd.DataFrame:
        rows: List[Dict[str, Any]] = []
        for analytic in analytics:
            total: int = analytic.total if analytic.total > 0 else 1
            rows.append({
                "N": analytic.n,
                "Candidate Type": analytic.candidate_type.display_name,
                "Predicted (%)": f"{(analytic.total_predicted / total) * 100:.2f}%",
                "Beyond (%)": f"{(analytic.total_beyond / total) * 100:.2f}%",
                "Beyond (Non-unique) (%)": f"{(analytic.total_beyond_non_unique / total) * 100:.2f}%",
                "Hallucinations (%)": f"{(analytic.total_hallucinations / total) * 100:.2f}%",
                "Missed (%)": f"{(analytic.total_missed / total) * 100:.2f}%",
                "Unprocessed (%)": f"{(analytic.total_unprocessed / total) * 100:.2f}%",
                "Total": analytic.total
            })

        df: pd.DataFrame = pd.DataFrame(rows)
        df["Candidate Type"] = pd.Categorical(df["Candidate Type"], categories=[x.display_name for x in SudokuSimplifiedCandidateType], ordered=True)
        df = df.sort_values(by=["N", "Candidate Type"], ascending=[True, True])
        return df
