"""Statistical analysis helpers: ART ANOVA and result plots (Task 4.5 / 4.6)."""

from rag_service.statistics.art_anova import (
    EFFECT_A,
    EFFECT_B,
    EFFECT_INTERACTION,
    ArtAnovaError,
    aligned_ranks,
    art_anova,
    art_contrasts,
    benjamini_hochberg,
)
from rag_service.statistics.plots import (
    CHUNKING_ORDER,
    RETRIEVAL_ORDER,
    PlotError,
    generate_all,
    plot_heatmap,
    plot_interaction,
    plot_retrieval_bars,
)

__all__ = [
    "CHUNKING_ORDER",
    "RETRIEVAL_ORDER",
    "EFFECT_A",
    "EFFECT_B",
    "EFFECT_INTERACTION",
    "ArtAnovaError",
    "PlotError",
    "aligned_ranks",
    "art_anova",
    "art_contrasts",
    "benjamini_hochberg",
    "generate_all",
    "plot_heatmap",
    "plot_interaction",
    "plot_retrieval_bars",
]
