import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Dict, Any
from core.enums.sudoku_simplified_candidate_type import SudokuSimplifiedCandidateType
from webui.schemas.sudoku_inference_analysis_schema import SudokuInferenceAnalyticsSchema
from webui.services.sudoku_inference_service import SudokuInferenceService

class SudokuInferenceAnalyticsChartComponent:
    @classmethod
    def render(cls, bar_width: float = 0.15) -> None:
        analytics: List[SudokuInferenceAnalyticsSchema] = SudokuInferenceService.get_analytics()
        if not analytics:
            st.info("No analytics found.")
            return

        df: pd.DataFrame = cls.__get_dataframe(analytics)
        metrics: Dict[str, Any] = {
            "total_predicted": "Predicted",
            "total_beyond": "Beyond",
            "total_beyond_non_unique": "Beyond (Non-unique)",
            "total_hallucinations": "Hallucinations",
            "total_missed": "Missed",
            "total_unprocessed": "Unprocessed"
        }

        fig, ax = plt.subplots(figsize=(8, 5))
        for i, (metric_key, metric_value) in enumerate(metrics.items()):
            bars = ax.bar(
                x=[x + i * bar_width for x in range(len(df))],
                height=df[metric_key],
                width=bar_width,
                label=metric_value
            )

            for bar in bars:
                height: float = bar.get_height()
                if height > 0:
                    ax.text(
                        x=bar.get_x() + bar.get_width() / 2,
                        y=height + max(df[metric_key]) * 0.01,
                        s=f"{int(height)}",
                        ha="center",
                        va="bottom",
                        fontsize=8
                    )

        ax.set_xticks([x + ((len(metrics) - 1) / 2) * bar_width for x in range(len(df))])
        ax.set_xticklabels(df["label"], rotation=30, ha="right")
        ax.set_title("Sudoku Inference Analytics")
        ax.set_xlabel("Grid Size (N) x Candidate Type")
        ax.set_ylabel("Count")
        ax.legend()
        st.pyplot(fig)

    @classmethod
    def __get_dataframe(cls, analytics: List[SudokuInferenceAnalyticsSchema]) -> pd.DataFrame:
        df = pd.DataFrame([a.model_dump() for a in analytics])
        df["candidate_type"] = df["candidate_type"].apply(lambda x: x.display_name)
        df["candidate_type"] = pd.Categorical(df["candidate_type"], categories=[x.display_name for x in SudokuSimplifiedCandidateType], ordered=True)

        df = df.groupby(["n", "candidate_type"], as_index=False, observed=False).sum(numeric_only=True)
        df = df.sort_values(["n", "candidate_type"]).reset_index(drop=True)
        df["label"] = df.apply(lambda r: f"{r.n}×{r.n} – {r.candidate_type}", axis=1)
        return df
