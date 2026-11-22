#!/usr/bin/env python3
"""Streamlit evaluation dashboard (Task 3.6).

Shows the 16-configuration evaluation summary, filters per-item results by
experiment / source type / question category, compares the bot answer against
the ground-truth answer, and charts the headline metrics.

Usage:
    streamlit run scripts/dashboard.py

Every artifact is optional: before Phase 1/4 finish, the dashboard still opens
and explains which file is missing.
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag_service.experiments.dashboard import (  # noqa: E402
    available_values,
    build_item_table,
    filter_items,
    load_answers,
    load_details,
    load_ground_truth,
    load_summary,
    metric_means,
)

DATA = PROJECT_ROOT / "data"
SUMMARY_PATH = DATA / "analysis" / "evaluation_summary.csv"
DETAILS_PATH = DATA / "analysis" / "evaluation_details.json"
GROUND_TRUTH_PATH = DATA / "evaluation" / "ground_truth.json"
RESULTS_DIR = DATA / "results"

METRIC_LABELS = {
    "faithfulness_mean": "Faithfulness (RAGAS)",
    "hit_at_5": "Hit@5",
    "latency_ms_mean": "Latensi rata-rata (ms)",
}
PERCENT_METRICS = ("faithfulness_mean", "hit_at_5")


@st.cache_data(show_spinner=False)
def load_data():
    """Read every artifact once per Streamlit session."""
    summary = load_summary(SUMMARY_PATH)
    details = load_details(DETAILS_PATH)
    ground_truth = load_ground_truth(GROUND_TRUTH_PATH)
    answers = load_answers(RESULTS_DIR)
    items = build_item_table(details, ground_truth, answers)
    return summary, items


def render_metric_cards(summary: pd.DataFrame) -> None:
    means = metric_means(summary)
    values = dict(zip(means["metric"], means["value"]))
    columns = st.columns(len(METRIC_LABELS))
    for column, (metric, label) in zip(columns, METRIC_LABELS.items()):
        value = values.get(metric)
        column.metric(label, "—" if pd.isna(value) else f"{value:.3f}")


def render_summary(summary: pd.DataFrame) -> None:
    if summary.empty:
        st.info(
            "`data/analysis/evaluation_summary.csv` belum ada. "
            "Jalankan `scripts/run_experiments.py` lalu `scripts/evaluate.py`."
        )
        return

    render_metric_cards(summary)
    st.subheader("Tabel 16 konfigurasi")
    st.dataframe(summary, use_container_width=True, hide_index=True)

    st.subheader("Rata-rata metrik")
    for metric, label in METRIC_LABELS.items():
        if metric not in summary.columns:
            continue
        chart = summary.set_index("experiment_code")[metric].dropna()
        if not chart.empty:
            st.caption(label)
            st.bar_chart(chart)


def render_items(items: pd.DataFrame) -> None:
    if items.empty:
        st.info(
            "Belum ada detail per soal. Hasil muncul setelah "
            "`scripts/evaluate.py` menulis `data/analysis/evaluation_details.json`."
        )
        return

    codes = st.multiselect("Konfigurasi", available_values(items, "experiment_code"))
    source_types = st.multiselect("Tipe sumber", available_values(items, "source_type"))
    categories = st.multiselect("Kategori pertanyaan", available_values(items, "category"))

    filtered = filter_items(
        items, codes=codes, source_types=source_types, categories=categories
    )
    st.caption(f"{len(filtered)} dari {len(items)} baris")
    st.dataframe(filtered, use_container_width=True, hide_index=True)


def render_comparison(items: pd.DataFrame) -> None:
    if items.empty:
        st.info("Belum ada jawaban untuk dibandingkan.")
        return

    left, right = st.columns(2)
    code = left.selectbox("Konfigurasi", available_values(items, "experiment_code"))
    candidates = items[items["experiment_code"] == code]
    item_id = right.selectbox("Soal", candidates["id"].tolist())
    row = candidates[candidates["id"] == item_id].iloc[0]

    st.markdown(f"**Pertanyaan:** {row['question']}")
    st.markdown(f"**Kategori:** {row.get('category') or '—'} · "
                f"**Sumber:** {row.get('source_type') or '—'}")

    answer_column, truth_column = st.columns(2)
    answer_column.markdown("#### Jawaban bot")
    answer_column.write(row.get("answer") or "—")
    truth_column.markdown("#### Jawaban ground truth")
    truth_column.write(row.get("ground_truth_answer") or "—")

    scores = pd.DataFrame(
        [
            {"metrik": "Faithfulness", "nilai": row.get("faithfulness")},
            {"metrik": "Hit@5", "nilai": row.get("hit_at_5")},
            {"metrik": "MRR@5", "nilai": row.get("mrr_at_5")},
            {"metrik": "nDCG@5", "nilai": row.get("ndcg_at_5")},
            {"metrik": "Latensi (ms)", "nilai": row.get("latency_ms")},
        ]
    )
    st.dataframe(scores, use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(page_title="Dashboard Evaluasi RAG LPK MBJ", layout="wide")
    st.title("Dashboard Evaluasi RAG — LPK MBJ")
    st.caption("16 konfigurasi chunking × retrieval. Sumber: data/results + data/analysis.")

    summary, items = load_data()

    summary_tab, items_tab, compare_tab = st.tabs(
        ["Ringkasan", "Detail per Soal", "Perbandingan Jawaban"]
    )
    with summary_tab:
        render_summary(summary)
    with items_tab:
        render_items(items)
    with compare_tab:
        render_comparison(items)


if __name__ == "__main__":
    main()
