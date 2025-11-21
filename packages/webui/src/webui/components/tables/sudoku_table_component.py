import pandas as pd
import streamlit as st
from typing import List, Dict, Any
from webui.schemas.sudoku_schema import SudokuSchema
from webui.services.sudoku_service import SudokuService

class SudokuTableComponent:
    @classmethod
    def render(cls, page_size: int = 100) -> None:
        if "sudoku_table_page" not in st.session_state:
            st.session_state.sudoku_table_page = 0

        total_sudokus, sudokus = SudokuService.get_all(page=st.session_state.sudoku_table_page, size=page_size)
        df: pd.DataFrame = cls.__get_dataframe(sudokus)

        st.title("📊 Sudoku Table")
        st.dataframe(df, hide_index=True, use_container_width=True)
        st.divider()

        left_column, center_column, right_column = st.columns(3)
        with left_column:
            if st.button("⬅️ Previous", disabled=st.session_state.sudoku_table_page == 0, use_container_width=True):
                st.session_state.sudoku_table_page -= 1
                st.rerun()

        total_pages: int = (total_sudokus + page_size - 1) // page_size
        with center_column:
            st.markdown(
                body=f"<div style='text-align: center; padding: 8px 0;'><strong>Page {st.session_state.sudoku_table_page + 1} of {total_pages}</strong></div>",
                unsafe_allow_html=True
            )

        with right_column:
            if st.button("Next ➡️", disabled=st.session_state.sudoku_table_page + 1 >= total_pages, use_container_width=True):
                st.session_state.sudoku_table_page += 1
                st.rerun()

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
                "Succeeded (Nth Layer)": sudoku.inference.succeeded_nth_layer if sudoku.inference else "—",
                "Images": len(sudoku.images)
            })
        return pd.DataFrame(rows)
