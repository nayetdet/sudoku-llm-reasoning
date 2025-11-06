import base64
import io
import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

import streamlit as st

ROOT_DIR: Path = Path(__file__).resolve().parents[4]

def resolve_data_path() -> Path:
    candidates = (
        ROOT_DIR / "packages" / "api" / "data" / "data.db",
        ROOT_DIR / "packages" / "api" / "data" / "data.db.bak",
        ROOT_DIR / "data" / "data.db",
        ROOT_DIR / "data" / "data.db.bak",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


DATA_PATH: Path = resolve_data_path()


@dataclass(frozen=True)
class SudokuImageData:
    mime: str
    content: bytes


@dataclass(frozen=True)
class SudokuRecord:
    identifier: int
    size: int
    candidate_type: str
    figures: List[SudokuImageData]


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cursor = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    )
    return cursor.fetchone() is not None


def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cursor = conn.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def has_images_predicate(conn: sqlite3.Connection) -> str:
    clauses: List[str] = []
    if table_exists(conn, "sudoku_image"):
        clauses.append("EXISTS (SELECT 1 FROM sudoku_image si WHERE si.sudoku_id = sudoku.id)")
    if column_exists(conn, "sudoku", "image"):
        clauses.append("image IS NOT NULL")
    if not clauses:
        return "1 = 0"
    return f"({' OR '.join(clauses)})"


def load_filter_options() -> tuple[Sequence[int], Sequence[str]]:
    if not DATA_PATH.exists():
        return (), ()

    with sqlite3.connect(DATA_PATH) as conn:
        conn.row_factory = sqlite3.Row
        predicate = has_images_predicate(conn)
        if predicate == "1 = 0":
            return (), ()

        query_base = f"FROM sudoku WHERE {predicate}"
        sizes = tuple(
            row["n"]
            for row in conn.execute(f"SELECT DISTINCT n {query_base} ORDER BY n")
        )
        candidate_types = tuple(
            row["candidate_type"]
            for row in conn.execute(
                f"SELECT DISTINCT candidate_type {query_base} ORDER BY candidate_type"
            )
        )
    return sizes, candidate_types


def fetch_page(
    page: int,
    size: int,
    grid_size: Optional[int],
    candidate_type: Optional[str],
) -> tuple[List[SudokuRecord], int]:
    if not DATA_PATH.exists():
        return [], 0

    with sqlite3.connect(DATA_PATH) as conn:
        conn.row_factory = sqlite3.Row
        predicate = has_images_predicate(conn)
        if predicate == "1 = 0":
            return [], 0

        filters: List[str] = [predicate]
        params: List[object] = []

        if grid_size is not None:
            filters.append("n = ?")
            params.append(grid_size)

        if candidate_type is not None:
            filters.append("candidate_type = ?")
            params.append(candidate_type)

        where_clause: str = " AND ".join(filters)
        limit_clause: str = " ORDER BY id ASC LIMIT ? OFFSET ?"

        total: int = conn.execute(
            f"SELECT COUNT(*) FROM sudoku WHERE {where_clause}", params
        ).fetchone()[0]

        select_columns: List[str] = ["id", "n", "candidate_type"]
        legacy_column_available = column_exists(conn, "sudoku", "image")
        if legacy_column_available:
            select_columns.append("image")

        query_params: List[object] = [*params, size, page * size]
        rows: Sequence[sqlite3.Row] = conn.execute(
            f"SELECT {', '.join(select_columns)} FROM sudoku WHERE {where_clause}{limit_clause}",
            query_params,
        ).fetchall()

        if not rows:
            return [], total

        has_image_table = table_exists(conn, "sudoku_image")
        images_by_sudoku: Dict[int, List[SudokuImageData]] = {
            row["id"]: [] for row in rows
        }

        if has_image_table:
            placeholders = ",".join("?" for _ in rows)
            sudoku_ids = [row["id"] for row in rows]
            image_rows = conn.execute(
                f"SELECT sudoku_id, mime, content FROM sudoku_image WHERE sudoku_id IN ({placeholders}) ORDER BY id",
                sudoku_ids,
            ).fetchall()

            for image_row in image_rows:
                content = image_row["content"]
                if isinstance(content, memoryview):
                    content = content.tobytes()
                images_by_sudoku[image_row["sudoku_id"]].append(
                    SudokuImageData(
                        mime=image_row["mime"] or "image/png",
                        content=content,
                    )
                )

        records: List[SudokuRecord] = []
        for row in rows:
            figures: List[SudokuImageData] = list(images_by_sudoku.get(row["id"], []))
            if not figures and legacy_column_available:
                legacy_blob = row["image"]
                if isinstance(legacy_blob, memoryview):
                    legacy_blob = legacy_blob.tobytes()

            records.append(
                SudokuRecord(
                    identifier=row["id"],
                    size=row["n"],
                    candidate_type=row["candidate_type"],
                    figures=figures,
                )
            )

        return records, total


def format_candidate_label(value: str) -> str:
    return value.replace("_", " ").title()


def build_figure_gallery(figures: Iterable[SudokuImageData]) -> str:
    figure_tags: List[str] = []
    for index, figure in enumerate(figures, start=1):
        encoded = base64.b64encode(figure.content).decode()
        figure_tags.append(
            f'<div class="figure-item"><img src="data:{figure.mime};base64,{encoded}" alt="Figura {index}" /></div>'
        )
    if figure_tags:
        return f'<div class="figure-gallery">{"".join(figure_tags)}</div>'
    return '<div class="figure-empty">Nenhuma figura disponível.</div>'


def render_record(record: SudokuRecord) -> None:
    candidate_label = format_candidate_label(record.candidate_type)
    gallery_html = build_figure_gallery(record.figures)

    st.markdown(
        f"""
        <div class="sudoku-card">
            <div class="sudoku-header">
                <div class="sudoku-title">Sudoku #{record.identifier}</div>
                <div class="sudoku-meta">{record.size}x{record.size} · {candidate_label}</div>
            </div>
            {gallery_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            color-scheme: dark;
        }
        body {
            background: radial-gradient(circle at top, #0f172a, #020617);
        }
        .stApp {
            background: transparent !important;
        }
        .sudoku-card {
            margin-bottom: 1.75rem;
            padding: 1.5rem;
            border-radius: 1.25rem;
            background: linear-gradient(130deg, rgba(15,23,42,0.92), rgba(30,41,59,0.9));
            border: 1px solid rgba(148, 163, 184, 0.25);
            box-shadow: 0 24px 60px rgba(2, 6, 23, 0.55);
        }
        .sudoku-header {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }
        .sudoku-title {
            font-size: 1.35rem;
            font-weight: 700;
            color: #e2e8f0;
        }
        .sudoku-meta {
            font-size: 0.95rem;
            letter-spacing: 0.04em;
            color: rgba(226, 232, 240, 0.75);
        }
        .figure-gallery {
            display: flex;
            gap: 1rem;
            overflow-x: auto;
            padding: 0.5rem 0.25rem 0.25rem;
        }
        .figure-gallery::-webkit-scrollbar {
            height: 8px;
        }
        .figure-gallery::-webkit-scrollbar-thumb {
            background: rgba(94, 234, 212, 0.45);
            border-radius: 999px;
        }
        .figure-item img {
            border-radius: 1rem;
            max-height: 320px;
            border: 1px solid rgba(148, 163, 184, 0.35);
            box-shadow: 0 18px 45px rgba(8, 15, 35, 0.65);
        }
        .figure-empty {
            margin-top: 1rem;
            color: rgba(226, 232, 240, 0.7);
            font-size: 0.95rem;
        }
        .filters-box {
            padding: 1.25rem;
            border-radius: 1rem;
            background: rgba(15, 23, 42, 0.82);
            border: 1px solid rgba(148, 163, 184, 0.2);
            margin-bottom: 1.5rem;
        }
        .pagination-bar {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1rem;
            margin: 0.5rem 0 1.5rem;
        }
        .pagination-button button {
            padding: 0.4rem 0.9rem;
            border-radius: 0.75rem;
            border: 1px solid rgba(94, 234, 212, 0.5);
            background: rgba(94, 234, 212, 0.08);
            color: #5eead4;
            font-weight: 600;
        }
        .pagination-button button:disabled {
            border-color: rgba(148, 163, 184, 0.2);
            color: rgba(148, 163, 184, 0.5);
            background: rgba(30, 41, 59, 0.6);
        }
        .pagination-info {
            font-size: 0.95rem;
            color: rgba(226, 232, 240, 0.7);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(
        page_title="Sudoku Figures Viewer",
        page_icon="🧩",
        layout="wide",
    )
    inject_styles()

    st.title("Sudoku Figures Viewer")
    st.caption("Visualize figuras geradas para sudokus classificados por estratégia.")

    if "page" not in st.session_state:
        st.session_state["page"] = 0

    sizes, candidate_types = load_filter_options()
    size_options = ["Todos"] + [f"{size}x{size}" for size in sizes]
    candidate_labels = ["Todos"] + [format_candidate_label(ct) for ct in candidate_types]

    with st.sidebar:
        st.markdown("### Filtros")
        selected_size_label = st.selectbox("Tamanho", size_options)
        selected_candidate_label = st.selectbox("Tipo de candidato", candidate_labels)
        page_size_value = st.selectbox("Sudokus por página", [1, 2, 3], index=1)

    size_map = {f"{size}x{size}": size for size in sizes}
    candidate_map = dict(zip(candidate_labels[1:], candidate_types))

    size_filter = size_map.get(selected_size_label)
    candidate_filter = candidate_map.get(selected_candidate_label)

    current_filters = (size_filter, candidate_filter, page_size_value)
    previous_filters = st.session_state.get("filters")
    if previous_filters != current_filters:
        st.session_state["page"] = 0
        st.session_state["filters"] = current_filters

    current_page = st.session_state["page"]

    records, total = fetch_page(
        page=current_page,
        size=page_size_value,
        grid_size=size_filter,
        candidate_type=candidate_filter,
    )

    total_pages = max(1, math.ceil(total / page_size_value)) if total else 1
    if current_page >= total_pages:
        st.session_state["page"] = total_pages - 1
        current_page = st.session_state["page"]
        records, total = fetch_page(
            page=current_page,
            size=page_size_value,
            grid_size=size_filter,
            candidate_type=candidate_filter,
        )
        total_pages = max(1, math.ceil(total / page_size_value)) if total else 1

    pagination_cols = st.columns([1, 1, 2, 1, 1], gap="small")
    with pagination_cols[1]:
        if st.button("◀", disabled=current_page == 0, key="prev-page"):
            st.session_state["page"] = max(0, current_page - 1)
            st.rerun()
    with pagination_cols[2]:
        st.markdown(
            f'<div class="pagination-info">Página {current_page + 1} de {total_pages} '
            f"· {total} sudokus</div>",
            unsafe_allow_html=True,
        )
    with pagination_cols[3]:
        if st.button(
            "▶",
            disabled=current_page >= total_pages - 1,
            key="next-page",
        ):
            st.session_state["page"] = min(total_pages - 1, current_page + 1)
            st.rerun()

    if not records:
        st.info("Nenhum sudoku com figuras encontrado para os filtros selecionados.")
        return

    for record in records:
        render_record(record)

if __name__ == "__main__":
    main()
