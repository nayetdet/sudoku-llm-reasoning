import pandas as pd
import streamlit as st
from typing import List, Dict, Any
from webui.components.sudoku.filters.sudoku_filter_component import SudokuFilterComponent
from webui.schemas.sudoku_schema import SudokuSchema
from webui.services.sudoku_service import SudokuService

class SudokuTableComponent:
    @classmethod
    def render(cls) -> None:
        st.title("📊 Sudoku")
        st.divider()

        sudoku_filters: Dict[str, Any] = SudokuFilterComponent.render(session_key_prefix="sudoku_table")
        sudokus = SudokuService.get_all_pages(**sudoku_filters)
        if not sudokus:
            st.info("No sudokus found.")
            return

        df: pd.DataFrame = cls.__get_dataframe(sudokus)
        st.dataframe(df, hide_index=True,  width="stretch")

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
