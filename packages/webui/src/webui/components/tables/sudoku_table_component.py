import pandas as pd
import streamlit as st
from typing import List, Dict, Any
from webui.schemas.sudoku_schema import SudokuSchema
from webui.services.sudoku_service import SudokuService

class SudokuTableComponent:
    @classmethod
    def render(cls) -> None:
        sudokus = SudokuService.get_all_pages()
        if not sudokus:
            st.info("No sudokus found.")
            return

        df: pd.DataFrame = cls.__get_dataframe(sudokus)
        st.title("📊 Sudoku")
        filtered_df: pd.DataFrame = cls.__filter_dataframe(df)
        st.dataframe(filtered_df, hide_index=True,  width="stretch")

    @classmethod
    def __get_dataframe(cls, sudokus: List[SudokuSchema]) -> pd.DataFrame:
        rows: List[Dict[str, Any]] = []
        for sudoku in sudokus:
            rows.append({
                "ID": sudoku.id,
                "N": sudoku.n,
                "Candidate Type": sudoku.candidate_type.display_name,
                "Grid": str(sudoku.grid),
                "Succeeded": sudoku.inference.succeeded if sudoku.inference else "—",
                "Succeeded (Nth Layer)": sudoku.inference.succeeded_nth_layer if sudoku.inference else "—"
            })
        return pd.DataFrame(rows)

    @classmethod
    def __filter_dataframe(cls, df: pd.DataFrame) -> pd.DataFrame:
        candidate_types = sorted(df["Candidate Type"].unique())
        selected_types = st.multiselect(
            "Filtrar por tipo de candidato",
            candidate_types,
            default=candidate_types,
            key="sudoku_candidate_filter",
        )
        if selected_types:
            return df[df["Candidate Type"].isin(selected_types)]
        return df
