"""Is the testbed capable of showing the effect being studied?

A null result means nothing if the mechanism under test does no work on
the instances used.  Asking "does adapting the evaporation rate help?" on
a graph where pheromone contributes nothing measures the noise floor and
reports it as a finding about adaptation.

Measured here: on a 30-node Erdos-Renyi graph of mean degree ~18,
disabling pheromone entirely (alpha = 0) changes excess by -0.15
percentage points, p = 0.91 — the colony's collective memory is doing
nothing, because almost any goal-directed walk finds a good route.  On a
200-node geometric graph the same intervention costs 15.6 points,
p < 0.001.

So the small tier is a demo and a debugging aid, not a testbed for any
claim about pheromone.  These tests keep that distinction enforced rather
than remembered.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy import stats as scipy_stats

from dynaswarm.config import BudgetCfg, Config, ControlCfg, ExperimentCfg, GraphCfg, ScenarioCfg
from dynaswarm.harness.trial import run_trial

#: The tier on which mechanism-level claims may be made.
SCIENCE_GRAPH = GraphCfg(model="geometric", n_nodes=200, density=0.04)

#: Fast, and deliberately not used for such claims.
DEMO_GRAPH = GraphCfg(model="erdos_renyi", n_nodes=30, density=0.3)


def excess_per_trial(graph: GraphCfg, params: dict[str, float], n: int = 8) -> np.ndarray:
    cfg = Config(
        graph=graph,
        scenario=ScenarioCfg(name="probe", churn=0.015, timesteps=35),
        experiment=ExperimentCfg(n_trials=n),
        budget=BudgetCfg(evaluations=300),
        control=ControlCfg(fixed_params=params),
    )
    scores = []
    for trial in range(n):
        rows = run_trial(cfg, trial, ["aco"]).steps
        values = [r.excess for r in rows if r.excess is not None]
        if values:
            scores.append(float(np.mean(values)))
    return np.array(scores)


@pytest.mark.slow
def test_pheromone_contributes_on_the_science_tier():
    """Removing the trail must measurably hurt, or the tier proves nothing.

    This is the precondition for every claim the project makes about
    adapting a pheromone parameter.  If disabling pheromone altogether
    costs nothing, then tuning or adapting its evaporation rate cannot
    matter either, and a null result would be a property of the testbed
    rather than of adaptation.
    """
    with_trail = excess_per_trial(SCIENCE_GRAPH, {})
    without = excess_per_trial(SCIENCE_GRAPH, {"alpha": 0.0})

    _, p_value = scipy_stats.wilcoxon(with_trail, without)
    assert without.mean() > with_trail.mean(), (
        f"disabling pheromone did not hurt ({without.mean():.2%} vs "
        f"{with_trail.mean():.2%}); this tier cannot support a claim about it"
    )
    assert p_value < 0.05, f"pheromone contribution not detectable here (p={p_value:.3f})"


@pytest.mark.slow
def test_the_demo_tier_is_too_easy_for_mechanism_claims():
    """The small graph is a debugging aid, and is documented as one.

    Asserted rather than noted because the tempting mistake is to reach
    for the fast configuration when running an experiment.  If this ever
    starts failing — because the tier got harder, or the budget smaller —
    the note in the docs has gone stale and should be revisited.
    """
    with_trail = excess_per_trial(DEMO_GRAPH, {})
    without = excess_per_trial(DEMO_GRAPH, {"alpha": 0.0})
    _, p_value = scipy_stats.wilcoxon(with_trail, without)
    assert p_value > 0.05, (
        "pheromone now has a detectable effect on the demo tier "
        f"(p={p_value:.3f}); the guidance that it is too easy needs revisiting"
    )


def test_goal_direction_is_inert_without_coordinates():
    """``goal_weight`` scales a distance term that does not exist on
    non-spatial graphs, so it is genuinely a no-op there.

    Worth pinning down: a tuner given this parameter on an Erdos-Renyi
    graph will happily search the dimension and report a confident value
    for it, and that value means nothing.
    """
    a = excess_per_trial(DEMO_GRAPH, {"goal_weight": 0.0}, n=4)
    b = excess_per_trial(DEMO_GRAPH, {"goal_weight": 5.0}, n=4)
    np.testing.assert_array_equal(a, b)


@pytest.mark.slow
def test_goal_direction_matters_where_coordinates_exist():
    with_goal = excess_per_trial(SCIENCE_GRAPH, {})
    without = excess_per_trial(SCIENCE_GRAPH, {"goal_weight": 0.0})
    _, p_value = scipy_stats.wilcoxon(with_goal, without)
    assert without.mean() > with_goal.mean()
    assert p_value < 0.05
