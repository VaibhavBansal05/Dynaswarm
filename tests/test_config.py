"""Configuration invariants.

The guard that matters here is compositional: every group option must
instantiate its typed schema.  A key describing a component nobody built
— a ``controller.patience`` that no code reads, say — cannot survive,
because the dataclass fields *are* the constructor arguments.
"""

from __future__ import annotations

import itertools
from pathlib import Path

import pytest
from hydra import compose, initialize_config_dir
from hydra.core.config_store import ConfigStore
from omegaconf import OmegaConf

from dynaswarm.config import Config, ExperimentCfg, register

CONF_DIR = str(Path(__file__).resolve().parents[1] / "conf")

register()


def _group_options(group: str) -> list[str]:
    repo = ConfigStore.instance().repo
    return sorted(name.removesuffix(".yaml") for name in repo[group])


def test_groups_are_populated():
    for group in ("graph", "scenario", "experiment", "budget"):
        assert _group_options(group), f"group {group} has no options"


@pytest.mark.parametrize(
    ("graph", "scenario"),
    list(itertools.product(_group_options("graph"), _group_options("scenario"))),
)
def test_every_combination_composes(graph: str, scenario: str):
    """Every group option must compose and instantiate its schema."""
    with initialize_config_dir(version_base=None, config_dir=CONF_DIR):
        cfg = compose(
            config_name="config",
            overrides=[f"graph={graph}", f"scenario={scenario}"],
        )
        obj = OmegaConf.to_object(cfg)
        assert isinstance(obj, Config)


def test_unknown_key_is_rejected():
    """A typo must fail at compose time, not be silently ignored."""
    with (
        initialize_config_dir(version_base=None, config_dir=CONF_DIR),
        pytest.raises(Exception),  # noqa: B017 - Hydra raises several types
    ):
        compose(config_name="config", overrides=["graph.nnodes=50"])


def test_tune_and_eval_seeds_are_disjoint():
    """Tuning on evaluation seeds inflates the baseline it is meant to test.

    Selecting the best of many candidates on the same seeds it is then
    reported on turns the headline figure into a maximum over noise
    rather than an estimate of performance.
    """
    cfg = ExperimentCfg()
    assert not (set(cfg.tune_seeds) & set(cfg.eval_seeds))


def test_scenarios_span_a_range_of_churn():
    """Static must be genuinely static and the tiers must be ordered."""
    with initialize_config_dir(version_base=None, config_dir=CONF_DIR):
        churn = {}
        for name in _group_options("scenario"):
            cfg = compose(config_name="config", overrides=[f"scenario={name}"])
            churn[name] = cfg.scenario.churn
    assert churn["static"] == 0.0
    assert churn["low"] < churn["moderate"] < churn["high"]
