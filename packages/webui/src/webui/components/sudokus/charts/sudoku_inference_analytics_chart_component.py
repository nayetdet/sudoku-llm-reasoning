import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from typing import List
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
        metrics: List[str] = [
            "total_planned",
            "total_beyond",
            "total_hallucinations",
            "total_missed",
            "total_unprocessed"
        ]

        fig, ax = plt.subplots(figsize=(8, 5))
        for i, metric in enumerate(metrics):
            bars = ax.bar(
                x=[x + i * bar_width for x in range(len(df))],
                height=df[metric],
                width=bar_width,
                label=metric.replace("total_", "").capitalize()
            )

            for bar in bars:
                height: float = bar.get_height()
                if height > 0:
                    ax.text(
                        x=bar.get_x() + bar.get_width() / 2,
                        y=height + max(df[metric]) * 0.01,
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
