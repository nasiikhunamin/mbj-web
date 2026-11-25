"""Tests for the Python ART ANOVA implementation (Task 4.5)."""

import numpy as np
import pandas as pd
import pytest
from statsmodels.stats.multitest import multipletests

from rag_service.statistics.art_anova import (
    ArtAnovaError,
    aligned_ranks,
    art_anova,
    art_contrasts,
    benjamini_hochberg,
    complete_cases,
)


def make_frame(subjects=12, seed=0, a_effect=0.2, b_effect=0.0, interaction=0.0):
    rng = np.random.default_rng(seed)
    chunking = ["fixed", "recursive", "semantic", "structure_aware"]
    retrieval = ["dense", "sparse_bm25", "hybrid_rrf", "hybrid_rerank"]
    rows = []
    for subject in range(subjects):
        for i, a in enumerate(chunking):
            for j, b in enumerate(retrieval):
                value = 0.2 + a_effect * i + b_effect * j + interaction * i * j
                value += rng.normal(0, 0.05)
                rows.append(
                    {
                        "subject": f"q{subject:02d}",
                        "chunking": a,
                        "retrieval": b,
                        "faithfulness": value,
                    }
                )
    return pd.DataFrame(rows)


def analyse(frame):
    return art_anova(
        frame,
        subject="subject",
        factor_a="chunking",
        factor_b="retrieval",
        value="faithfulness",
    )


# ----------------------------------------------------------------------
# Benjamini-Hochberg
# ----------------------------------------------------------------------


def test_benjamini_hochberg_matches_statsmodels():
    pvalues = [0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205, 0.212, 0.216]
    expected = multipletests(pvalues, method="fdr_bh")[1]
    assert benjamini_hochberg(pvalues) == pytest.approx(expected.tolist())


def test_benjamini_hochberg_is_monotone_and_bounded():
    adjusted = benjamini_hochberg([0.9, 0.01, 0.5, 0.2])
    assert all(0 <= value <= 1 for value in adjusted)
    ordered = [adjusted[index] for index in np.argsort([0.9, 0.01, 0.5, 0.2])]
    assert ordered == sorted(ordered)


def test_benjamini_hochberg_empty():
    assert benjamini_hochberg([]) == []


# ----------------------------------------------------------------------
# Alignment / omnibus
# ----------------------------------------------------------------------


def test_aligned_ranks_are_a_permutation_of_one_to_n():
    frame = make_frame()
    ranks = aligned_ranks(
        frame, "subject", "chunking", "retrieval", "faithfulness", "a"
    )
    assert sorted(ranks.tolist()) == list(range(1, len(frame) + 1))


def test_art_anova_detects_chunking_effect():
    results = analyse(make_frame(a_effect=0.3))
    assert results["a"]["p"] < 0.01
    assert results["b"]["p"] > 0.05
    assert results["interaction"]["p"] > 0.05


def test_art_anova_detects_retrieval_effect():
    results = analyse(make_frame(a_effect=0.0, b_effect=0.3))
    assert results["b"]["p"] < 0.01
    assert results["a"]["p"] > 0.05


def test_art_anova_all_pvalues_in_range():
    results = analyse(make_frame())
    for effect in ("a", "b", "interaction"):
        assert 0.0 <= results[effect]["p"] <= 1.0
        assert results[effect]["F"] >= 0.0


def test_art_anova_rejects_unbalanced_design():
    frame = make_frame().drop(index=0)
    with pytest.raises(ArtAnovaError, match="unbalanced"):
        analyse(frame)


def test_art_anova_rejects_duplicate_cells():
    frame = make_frame()
    duplicated = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    with pytest.raises(ArtAnovaError, match="exactly one observation"):
        analyse(duplicated)


# ----------------------------------------------------------------------
# Listwise deletion of incomplete subjects
# ----------------------------------------------------------------------


def test_complete_cases_drops_subject_missing_one_cell():
    frame = make_frame()
    missing = frame[
        (frame["subject"] == "q00")
        & (frame["chunking"] == "fixed")
        & (frame["retrieval"] == "dense")
    ].index
    filtered, dropped = complete_cases(
        frame.drop(index=missing),
        subject="subject",
        factor_a="chunking",
        factor_b="retrieval",
    )

    assert dropped == ["q00"]
    assert filtered["subject"].nunique() == 11
    assert filtered.groupby("subject").size().eq(16).all()
    # The filtered frame must satisfy the balanced-design requirement.
    analyse(filtered)


def test_complete_cases_keeps_balanced_frame_unchanged():
    frame = make_frame()
    filtered, dropped = complete_cases(
        frame,
        subject="subject",
        factor_a="chunking",
        factor_b="retrieval",
    )

    assert dropped == []
    assert len(filtered) == len(frame)


def test_complete_cases_returns_empty_when_every_subject_is_incomplete():
    frame = make_frame()
    # Remove a different cell from every subject so no subject is complete.
    drop = frame.groupby("subject").head(1).index
    filtered, dropped = complete_cases(
        frame.drop(index=drop),
        subject="subject",
        factor_a="chunking",
        factor_b="retrieval",
    )

    assert filtered.empty
    assert len(dropped) == 12


# ----------------------------------------------------------------------
# Post-hoc contrasts
# ----------------------------------------------------------------------


def test_art_contrasts_returns_six_pairs_per_family():
    frame = make_frame(a_effect=0.3)
    for family in ("a", "b"):
        table = art_contrasts(
            frame,
            subject="subject",
            factor_a="chunking",
            factor_b="retrieval",
            value="faithfulness",
            family=family,
        )
        assert len(table) == 6
        assert {"family", "pair", "t", "p", "p_adjusted"} <= set(table.columns)
        assert (table["p_adjusted"] >= table["p"] - 1e-9).all()


def test_art_contrasts_rejects_unknown_family():
    with pytest.raises(ArtAnovaError):
        art_contrasts(
            make_frame(),
            subject="subject",
            factor_a="chunking",
            factor_b="retrieval",
            value="faithfulness",
            family="c",
        )
