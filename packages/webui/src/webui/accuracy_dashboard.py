import os
from typing import Any, Dict, List

import altair as alt
import pandas as pd
import requests
import streamlit as st


API_BASE_URL: str = os.getenv("SUDOKU_API_BASE_URL", "http://localhost:8000/v1").rstrip("/")


@st.cache_data(ttl=30)
def fetch_accuracy_results() -> List[Dict[str, Any]]:
    url = f"{API_BASE_URL}/reasoner/accuracy"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.json()


def build_dataframe(records: List[Dict[str, Any]]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for entry in records:
        rows.append(
            {
                "Técnica": entry["technique"],
                "Execuções": entry["sample_size"],
                "Acertos": entry["success_count"],
                "Acurácia (%)": round(entry["accuracy"] * 100, 2),
                "Atualizado em": pd.to_datetime(entry["updated_at"]).strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    st.set_page_config(page_title="Acurácia do Sudoku Reasoner", layout="centered")
    st.title("Dashboard de Acurácia — Sudoku Reasoner")
    st.caption("Leitura direta da API. Atualize após rodar os testes para ver os novos resultados.")

    if st.button("Atualizar métricas"):
        fetch_accuracy_results.clear()

    try:
        records = fetch_accuracy_results()
    except requests.RequestException as exc:
        st.error(f"Não foi possível consultar a API ({exc}). Verifique se ela está em execução em {API_BASE_URL}.")
        return

    if not records:
        st.info("Nenhuma métrica registrada ainda. Execute os testes para gerar os dados.")
        return

    df = build_dataframe(records)

    st.subheader("Resumo rápido")
    num_columns = min(3, len(df))
    columns = st.columns(num_columns)
    for column, (_, row) in zip(columns, df.iterrows()):
        column.metric(
            label=row["Técnica"],
            value=f"{row['Acurácia (%)']:.2f}%",
            delta=f"{row['Acertos']}/{row['Execuções']} acertos",
        )

    st.subheader("Acurácia por técnica")
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6, color="#4BA3C3")
        .encode(
            x=alt.X("Acurácia (%)", scale=alt.Scale(domain=[0, 100])),
            y=alt.Y("Técnica", sort="-x"),
            tooltip=[
                alt.Tooltip("Técnica"),
                alt.Tooltip("Acurácia (%)"),
                alt.Tooltip("Acertos"),
                alt.Tooltip("Execuções"),
                alt.Tooltip("Atualizado em"),
            ],
        )
    )
    text_layer = chart.mark_text(align="left", dx=3, color="#0F2E3D").encode(text=alt.Text("Acurácia (%)", format=".2f"))
    st.altair_chart((chart + text_layer).properties(height=260), use_container_width=True)

    st.subheader("Detalhes")
    st.dataframe(df, hide_index=True, use_container_width=True)


if __name__ == "__main__":
    main()
