"""Comparing arms honestly.

Three commitments, each guarding a way this kind of comparison goes
wrong.

**Pair on trials, not timesteps.**  Successive timesteps within a trial
share a graph and an event sequence, so they are strongly dependent.
Treating them as independent observations inflates the sample by the
trial length and shrinks every p-value accordingly — sixty correlated
steps masquerading as sixty samples will find significance almost
anywhere.

**Correct for the family.**  A signal-by-scenario grid runs a dozen
comparisons, and at alpha = 0.05 roughly one in twenty will look
significant by chance alone.  Holm is used rather than Bonferroni: it is
uniformly more powerful and equally valid, and it needs no assumption
about independence between tests.

**Report an effect size next to every p-value.**  Significance says a
difference is unlikely to be zero; it says nothing about whether the
difference matters.  With enough trials a tenth of a percentage point
clears any threshold.  Cliff's delta is used because it is
distribution-free, like the test it accompanies.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

__all__ = ["Comparison", "paired_compare", "holm_correct", "cliffs_delta", "compare_arms"]

#: Conventional thresholds for Cliff's delta.
_DELTA_LABELS = ((0.147, "negligible"), (0.33, "small"), (0.474, "medium"))


@dataclass
class Comparison:
    """One paired comparison between two arms.

    Attributes:
        label: What was compared.
        n_pairs: Trials contributing to both arms.
        mean_a: Mean for the first arm.
        mean_b: Mean for the second.
        delta: ``mean_a - mean_b``; negative favours the first when the
            metric is one where lower is better.
        p_value: Raw two-sided Wilcoxon signed-rank p-value.
        p_adjusted: After Holm correction across the family.
        effect: Cliff's delta.
        effect_label: Its conventional magnitude.
        significant: Whether the *adjusted* p-value clears alpha.
    """

    label: str
    n_pairs: int
    mean_a: float
    mean_b: float
    delta: float
    p_value: float
    p_adjusted: float = float("nan")
    effect: float = float("nan")
    effect_label: str = ""
    significant: bool = False


def cliffs_delta(a: np.ndarray, b: np.ndarray) -> tuple[float, str]:
    """Non-parametric effect size: how often one sample exceeds the other.

    Args:
        a: First sample.
        b: Second sample.

    Returns:
        ``(delta, label)`` with delta in ``[-1, 1]``; 0 means the samples
        are interleaved, and the sign follows ``a`` being larger.
    """
    if a.size == 0 or b.size == 0:
        return float("nan"), ""
    greater = int((a[:, None] > b[None, :]).sum())
    lesser = int((a[:, None] < b[None, :]).sum())
    delta = (greater - lesser) / (a.size * b.size)

    magnitude = abs(delta)
    label = "large"
    for bound, name in _DELTA_LABELS:
        if magnitude < bound:
            label = name
            break
    return float(delta), label


def paired_compare(a: np.ndarray, b: np.ndarray, label: str = "") -> Comparison:
    """Wilcoxon signed-rank test on paired samples.

    Args:
        a: First arm's per-trial values.
        b: Second arm's, aligned by trial.
        label: Description carried through to the result.

    Returns:
        The comparison, with adjustment left for :func:`holm_correct`.

    Raises:
        ValueError: If the samples differ in length, which would mean
            they are not actually paired.
    """
    if a.size != b.size:
        raise ValueError(f"paired samples must align: {a.size} versus {b.size}")

    finite = np.isfinite(a) & np.isfinite(b)
    a, b = a[finite], b[finite]

    if a.size < 2 or np.allclose(a, b):
        # An identical pair is not evidence of no effect; it usually
        # means one arm never moved, which is worth seeing as p = 1
        # rather than as a crash.
        p_value = 1.0
    else:
        _, p_value = scipy_stats.wilcoxon(a, b)

    effect, effect_label = cliffs_delta(a, b)
    return Comparison(
        label=label,
        n_pairs=int(a.size),
        mean_a=float(np.mean(a)) if a.size else float("nan"),
        mean_b=float(np.mean(b)) if b.size else float("nan"),
        delta=float(np.mean(a) - np.mean(b)) if a.size else float("nan"),
        p_value=float(p_value),
        effect=effect,
        effect_label=effect_label,
    )


def holm_correct(comparisons: list[Comparison], alpha: float = 0.05) -> list[Comparison]:
    """Apply Holm's step-down correction across a family of tests.

    Args:
        comparisons: Every test in the family — *all* of them.  Omitting
            the ones that came out uninteresting is what makes a
            correction meaningless.
        alpha: Family-wise error rate.

    Returns:
        The same comparisons with ``p_adjusted`` and ``significant`` set.
    """
    if not comparisons:
        return []

    order = sorted(range(len(comparisons)), key=lambda i: comparisons[i].p_value)
    m = len(comparisons)
    running = 0.0

    for rank, index in enumerate(order):
        item = comparisons[index]
        adjusted = min(1.0, (m - rank) * item.p_value)
        # Holm's adjusted values must not decrease down the ordering.
        running = max(running, adjusted)
        item.p_adjusted = running
        item.significant = running < alpha

    return comparisons


def compare_arms(
    frame: pd.DataFrame,
    arm_a: str,
    arm_b: str,
    metric: str = "mean_excess",
    within: tuple[str, ...] = ("scenario", "signal_kind"),
    alpha: float = 0.05,
) -> pd.DataFrame:
    """Compare two arms within every condition, corrected as one family.

    Args:
        frame: Per-trial rows, e.g. from
            :func:`~dynaswarm.analysis.load.per_trial_excess`.
        arm_a: First arm.
        arm_b: Second arm, the baseline.
        metric: Column to compare.
        within: Columns defining the conditions to compare inside.
        alpha: Family-wise error rate.

    Returns:
        One row per condition, with adjusted p-values and effect sizes.
    """
    keys = [k for k in within if k in frame.columns]
    comparisons: list[Comparison] = []
    contexts: list[dict] = []

    for values, group in frame.groupby(keys, sort=True) if keys else [((), frame)]:
        values = values if isinstance(values, tuple) else (values,)
        left = group[group.arm == arm_a].sort_values("trial")[metric].to_numpy(float)
        right = group[group.arm == arm_b].sort_values("trial")[metric].to_numpy(float)
        if left.size == 0 or right.size == 0:
            continue
        size = min(left.size, right.size)
        label = "/".join(str(v) for v in values) or "all"
        comparisons.append(paired_compare(left[:size], right[:size], label=label))
        contexts.append(dict(zip(keys, values, strict=True)))

    holm_correct(comparisons, alpha=alpha)

    return pd.DataFrame(
        [
            {
                **context,
                "metric": metric,
                "n_pairs": c.n_pairs,
                f"{arm_a}": c.mean_a,
                f"{arm_b}": c.mean_b,
                "delta": c.delta,
                "p_value": c.p_value,
                "p_holm": c.p_adjusted,
                "cliffs_delta": c.effect,
                "effect": c.effect_label,
                "significant": c.significant,
            }
            for context, c in zip(contexts, comparisons, strict=True)
        ]
    )
