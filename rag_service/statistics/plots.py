"""Publication figures for the RAG experiment results (Task 4.6).

Builds three figures from the aggregate summary CSV (Task 4.2):

* 4x4 heatmap: chunking x retrieval vs a chosen metric.
* grouped bar chart: retrieval metrics (Hit@5, MRR@5) per retrieval method.
* interaction plot: one line per retrieval method across the chunking levels.

All figures are exported as 300 DPI PNGs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Optional, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

CHUNKING_ORDER = ("fixed", "recursive", "semantic", "structure_aware")
RETRIEVAL_ORDER = ("dense", "sparse_bm25", "hybrid_rrf", "hybrid_rerank")
DEFAULT_DPI = 300


class PlotError(RuntimeError):
    """Raised when a figure cannot be produced from the given data."""


def _require(summary: pd.DataFrame, columns: Sequence[str]) -> None:
    if summary.empty:
        raise PlotError("summary is empty; run scripts/evaluate.py (Task 4.2) first")
    missing = [column for column in columns if column not in summary.columns]
    if missing:
        raise PlotError(f"summary is missing columns: {missing}")


def _ordered(values: Iterable[str], order: Sequence[str]) -> list:
    present = [value for value in order if value in set(values)]
    extras = sorted(set(values) - set(present))
    return present + extras


def _save(figure, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.tight_layout()
    figure.savefig(path, dpi=DEFAULT_DPI, bbox_inches="tight")
    plt.close(figure)
    return path


def plot_heatmap(
    summary: pd.DataFrame,
    metric: str = "faithfulness_mean",
    output: Optional[Path] = None,
) -> Path:
    """4x4 Chunking x Retrieval heatmap for ``metric``."""
    _require(summary, ["chunking_strategy", "retrieval_method", metric])
    pivot = summary.pivot_table(
        index="chunking_strategy",
        columns="retrieval_method",
        values=metric,
        aggfunc="mean",
    )
    pivot = pivot.reindex(index=_ordered(pivot.index, CHUNKING_ORDER))
    pivot = pivot.reindex(columns=_ordered(pivot.columns, RETRIEVAL_ORDER))

    figure, axes = plt.subplots(figsize=(7.5, 5.5))
    image = axes.imshow(pivot.to_numpy(dtype=float), cmap="viridis", aspect="auto")
    axes.set_xticks(range(len(pivot.columns)), labels=pivot.columns, rotation=30, ha="right")
    axes.set_yticks(range(len(pivot.index)), labels=pivot.index)
    for row in range(pivot.shape[0]):
        for column in range(pivot.shape[1]):
            value = pivot.iat[row, column]
            if pd.notna(value):
                axes.text(column, row, f"{value:.3f}", ha="center", va="center", color="white", fontsize=9)
    axes.set_xlabel("Metode Retrieval")
    axes.set_ylabel("Strategi Chunking")
    axes.set_title(f"Heatmap {metric}")
    figure.colorbar(image, ax=axes, label=metric)
    return _save(figure, output or Path("data/analysis/figures/heatmap.png"))


def plot_retrieval_bars(
    summary: pd.DataFrame,
    metrics: Sequence[str] = ("hit_at_5", "mrr_at_5"),
    output: Optional[Path] = None,
) -> Path:
    """Grouped bar chart of retrieval metrics per retrieval method."""
    _require(summary, ["retrieval_method", *metrics])
    grouped = (
        summary.groupby("retrieval_method")[list(metrics)]
        .mean()
        .reindex(_ordered(summary["retrieval_method"].unique(), RETRIEVAL_ORDER))
    )
    axes = grouped.plot(kind="bar", figsize=(8, 5), rot=0, width=0.8)
    axes.set_xlabel("Metode Retrieval")
    axes.set_ylabel("Skor rata-rata")
    axes.set_title("Perbandingan Metrik Retrieval")
    axes.legend(title="Metrik")
    axes.grid(axis="y", linestyle=":", alpha=0.5)
    return _save(axes.get_figure(), output or Path("data/analysis/figures/retrieval_metrics.png"))


def plot_interaction(
    summary: pd.DataFrame,
    metric: str = "faithfulness_mean",
    output: Optional[Path] = None,
) -> Path:
    """Interaction plot: one retrieval line across the chunking levels."""
    _require(summary, ["chunking_strategy", "retrieval_method", metric])
    chunking = _ordered(summary["chunking_strategy"].unique(), CHUNKING_ORDER)
    retrieval = _ordered(summary["retrieval_method"].unique(), RETRIEVAL_ORDER)
    pivot = summary.pivot_table(
        index="chunking_strategy", columns="retrieval_method", values=metric, aggfunc="mean"
    )
    pivot = pivot.reindex(index=chunking, columns=retrieval)

    figure, axes = plt.subplots(figsize=(8, 5))
    for method in retrieval:
        axes.plot(chunking, pivot[method].to_numpy(dtype=float), marker="o", label=method)
    axes.set_xlabel("Strategi Chunking")
    axes.set_ylabel(metric)
    axes.set_title(f"Interaction Plot: {metric}")
    axes.legend(title="Metode Retrieval")
    axes.grid(linestyle=":", alpha=0.5)
    return _save(figure, output or Path("data/analysis/figures/interaction.png"))


def generate_all(
    summary: pd.DataFrame,
    figures_dir: Path,
    metric: str = "faithfulness_mean",
) -> Dict[str, Path]:
    """Write every figure and return ``name -> path``."""
    figures_dir = Path(figures_dir)
    return {
        "heatmap": plot_heatmap(summary, metric, figures_dir / "heatmap.png"),
        "retrieval_metrics": plot_retrieval_bars(
            summary, output=figures_dir / "retrieval_metrics.png"
        ),
        "interaction": plot_interaction(
            summary, metric, figures_dir / "interaction.png"
        ),
    }
