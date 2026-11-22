"""Tests for the publication figure generator (Task 4.6)."""

import pandas as pd
import pytest

from rag_service.statistics.plots import (
    PlotError,
    generate_all,
    plot_heatmap,
    plot_interaction,
    plot_retrieval_bars,
)

CHUNKING = ("fixed", "recursive", "semantic", "structure_aware")
RETRIEVAL = ("dense", "sparse_bm25", "hybrid_rrf", "hybrid_rerank")


def make_summary():
    rows = []
    code = 0
    for chunk_index, chunking in enumerate(CHUNKING):
        for retrieval_index, retrieval in enumerate(RETRIEVAL):
            code += 1
            rows.append(
                {
                    "experiment_code": f"E{code:02d}",
                    "chunking_strategy": chunking,
                    "retrieval_method": retrieval,
                    "faithfulness_mean": 0.4 + 0.05 * chunk_index + 0.01 * retrieval_index,
                    "hit_at_5": 0.5 + 0.1 * retrieval_index,
                    "mrr_at_5": 0.4 + 0.08 * retrieval_index,
                    "latency_ms_mean": 2000 + 100 * code,
                }
            )
    return pd.DataFrame(rows)


def assert_png(path):
    assert path.exists()
    assert path.stat().st_size > 1000


def test_plot_heatmap(tmp_path):
    assert_png(plot_heatmap(make_summary(), output=tmp_path / "heatmap.png"))


def test_plot_retrieval_bars(tmp_path):
    assert_png(plot_retrieval_bars(make_summary(), output=tmp_path / "bars.png"))


def test_plot_interaction(tmp_path):
    assert_png(plot_interaction(make_summary(), output=tmp_path / "interaction.png"))


def test_generate_all_writes_three_figures(tmp_path):
    figures = generate_all(make_summary(), tmp_path / "figures")
    assert set(figures) == {"heatmap", "retrieval_metrics", "interaction"}
    for path in figures.values():
        assert_png(path)


def test_empty_summary_raises():
    with pytest.raises(PlotError):
        plot_heatmap(pd.DataFrame())


def test_missing_column_raises():
    summary = make_summary().drop(columns=["faithfulness_mean"])
    with pytest.raises(PlotError, match="missing columns"):
        plot_heatmap(summary)


def test_custom_metric(tmp_path):
    path = plot_heatmap(make_summary(), metric="hit_at_5", output=tmp_path / "hit.png")
    assert_png(path)
