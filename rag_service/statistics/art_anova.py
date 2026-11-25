"""Aligned Rank Transform (ART) ANOVA in Python (Task 4.5).

Python has no official ARTool port, so this module implements the Wobbrock et
al. (2011) Aligned Rank Transform for a fully within-subjects two-way design:

1. For each effect, align the response by removing every other effect
   (``aligned = residuals + contribution_of_the_effect``).
2. Rank the aligned responses (average ranks for ties).
3. Run a repeated-measures ANOVA (``statsmodels`` ``AnovaRM``) on the ranks.

Post-hoc pairwise contrasts run paired t-tests on the aligned ranks and are
corrected per family with Benjamini-Hochberg.

Scientific caveat: this is an independent reimplementation, not the reference
ARTool package. Results are reported as-is without cross-checking against
ARTool; the project's external validation relies on the inter-annotator
agreement computed in Task 4.4 (percent agreement 95.41%).
See ``tasks/todo.md`` Task 4.5.
"""

from __future__ import annotations

from itertools import combinations
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy import stats

EFFECT_A = "a"
EFFECT_B = "b"
EFFECT_INTERACTION = "interaction"
TERMS = (EFFECT_A, EFFECT_B, EFFECT_INTERACTION)


class ArtAnovaError(RuntimeError):
    """Raised when the ART ANOVA cannot be computed on the given data."""


def benjamini_hochberg(pvalues: Sequence[float]) -> List[float]:
    """Return Benjamini-Hochberg FDR-adjusted p-values, preserving order."""
    values = [float(p) for p in pvalues]
    count = len(values)
    if count == 0:
        return []

    order = sorted(range(count), key=lambda index: values[index])
    adjusted = [0.0] * count
    previous = 1.0
    for rank, index in enumerate(reversed(order), start=1):
        # rank from the largest p-value downwards
        position = count - rank + 1
        candidate = min(previous, values[index] * count / position)
        adjusted[index] = candidate
        previous = candidate
    return adjusted


def _validate(data: pd.DataFrame, subject: str, factor_a: str, factor_b: str, value: str) -> None:
    for column in (subject, factor_a, factor_b, value):
        if column not in data.columns:
            raise ArtAnovaError(f"missing required column: {column!r}")

    frame = data[[subject, factor_a, factor_b, value]].dropna()
    if frame.empty:
        raise ArtAnovaError("no complete observations after dropping nulls")

    counts = frame.groupby([subject, factor_a, factor_b])[value].size()
    if (counts > 1).any():
        raise ArtAnovaError(
            "each subject x factor_a x factor_b cell must hold exactly one observation"
        )

    n_a = frame[factor_a].nunique()
    n_b = frame[factor_b].nunique()
    expected_cells = n_a * n_b
    per_subject = frame.groupby(subject).size()
    if not (per_subject == expected_cells).all():
        raise ArtAnovaError(
            "design is unbalanced: every subject must appear in all "
            f"{expected_cells} factor combinations"
        )


def complete_cases(
    data: pd.DataFrame,
    *,
    subject: str,
    factor_a: str,
    factor_b: str,
) -> Tuple[pd.DataFrame, List[str]]:
    """Keep only subjects observed in every factor combination (listwise deletion).

    The ART ANOVA requires a balanced within-subject design. When one metric is
    missing for a configuration — for example a faithfulness score is skipped
    because the system refused an in-domain question — dropping only that row
    would leave the subject with fewer than ``n_a * n_b`` cells and the ANOVA
    would fail. This helper removes the whole subject instead, so every retained
    subject contributes exactly one observation per cell.

    Returns ``(filtered_frame, dropped_subject_ids)``. The subject ids are
    returned as strings so they can be written straight to JSON.
    """
    for column in (subject, factor_a, factor_b):
        if column not in data.columns:
            raise ArtAnovaError(f"missing required column: {column!r}")

    frame = data[[subject, factor_a, factor_b]].dropna()
    if frame.empty:
        return data.iloc[0:0].copy(), []

    levels_a = frame[factor_a].unique()
    levels_b = frame[factor_b].unique()
    expected_cells = len(levels_a) * len(levels_b)

    cells = frame.drop_duplicates([subject, factor_a, factor_b])
    per_subject = cells.groupby(subject).size()
    complete = set(per_subject[per_subject == expected_cells].index)
    all_subjects = set(frame[subject].unique())
    dropped = sorted((str(value) for value in all_subjects - complete))

    filtered = data[data[subject].isin(complete)].copy()
    return filtered, dropped


def _design(data: pd.DataFrame, factor_a: str, factor_b: str) -> pd.DataFrame:
    import patsy

    return patsy.dmatrix(
        f"C({factor_a}, Sum) * C({factor_b}, Sum)",
        data,
        return_type="dataframe",
    )


def aligned_ranks(
    data: pd.DataFrame,
    subject: str,
    factor_a: str,
    factor_b: str,
    value: str,
    target: str,
) -> pd.Series:
    """Align ``value`` for ``target`` and return average ranks in row order."""
    frame = data.reset_index(drop=True)
    design = _design(frame, factor_a, factor_b)
    matrix = design.to_numpy(dtype=float)
    observed = frame[value].to_numpy(dtype=float)

    beta, *_ = np.linalg.lstsq(matrix, observed, rcond=None)
    residuals = observed - matrix @ beta

    if target == EFFECT_INTERACTION:
        selected = [":" in column for column in design.columns]
    elif target == EFFECT_A:
        selected = [
            column.startswith(f"C({factor_a},") and ":" not in column
            for column in design.columns
        ]
    elif target == EFFECT_B:
        selected = [
            column.startswith(f"C({factor_b},") and ":" not in column
            for column in design.columns
        ]
    else:
        raise ArtAnovaError(f"unknown effect: {target!r}")

    contribution = design.to_numpy(dtype=float)[:, selected] @ beta[selected]
    aligned = residuals + contribution
    return pd.Series(stats.rankdata(aligned), index=frame.index, name="__rank__")


def _term_name(factor_a: str, factor_b: str, target: str) -> str:
    if target == EFFECT_A:
        return factor_a
    if target == EFFECT_B:
        return factor_b
    return f"{factor_a}:{factor_b}"


def art_anova(
    data: pd.DataFrame,
    *,
    subject: str,
    factor_a: str,
    factor_b: str,
    value: str,
) -> Dict[str, Dict[str, float]]:
    """Run the two-way within-subject ART ANOVA.

    Returns ``{"a": {"F":..., "p":...}, "b": {...}, "interaction": {...}}``.
    """
    from statsmodels.stats.anova import AnovaRM

    _validate(data, subject, factor_a, factor_b, value)
    frame = data[[subject, factor_a, factor_b, value]].dropna().reset_index(drop=True)

    results: Dict[str, Dict[str, float]] = {}
    for target in TERMS:
        ranked = frame.copy()
        ranked["__rank__"] = aligned_ranks(
            frame, subject, factor_a, factor_b, value, target
        )
        table = AnovaRM(
            ranked, "__rank__", subject, within=[factor_a, factor_b]
        ).fit().anova_table
        term = _term_name(factor_a, factor_b, target)
        if term not in table.index:
            raise ArtAnovaError(f"term {term!r} missing from ANOVA table: {list(table.index)}")
        results[target] = {
            "F": float(table.loc[term, "F Value"]),
            "p": float(table.loc[term, "Pr > F"]),
        }
    return results


def art_contrasts(
    data: pd.DataFrame,
    *,
    subject: str,
    factor_a: str,
    factor_b: str,
    value: str,
    family: str,
) -> pd.DataFrame:
    """Paired contrasts on aligned ranks for one factor family, BH-corrected."""
    if family not in (EFFECT_A, EFFECT_B):
        raise ArtAnovaError(f"family must be {EFFECT_A!r} or {EFFECT_B!r}")

    _validate(data, subject, factor_a, factor_b, value)
    frame = data[[subject, factor_a, factor_b, value]].dropna().reset_index(drop=True)
    factor = factor_a if family == EFFECT_A else factor_b
    frame = frame.assign(rank=aligned_ranks(frame, subject, factor_a, factor_b, value, family))

    levels = sorted(frame[factor].unique())
    rows: List[Dict[str, Any]] = []
    for left, right in combinations(levels, 2):
        left_values = (
            frame[frame[factor] == left].groupby(subject)["rank"].mean()
        )
        right_values = (
            frame[frame[factor] == right].groupby(subject)["rank"].mean()
        )
        paired = pd.concat([left_values, right_values], axis=1).dropna()
        statistic, pvalue = stats.ttest_rel(paired.iloc[:, 0], paired.iloc[:, 1])
        rows.append(
            {
                "family": factor,
                "pair": f"{left} vs {right}",
                "t": float(statistic),
                "p": float(pvalue),
            }
        )

    if not rows:
        return pd.DataFrame(columns=["family", "pair", "t", "p", "p_adjusted"])

    table = pd.DataFrame(rows)
    table["p_adjusted"] = benjamini_hochberg(table["p"].tolist())
    return table
