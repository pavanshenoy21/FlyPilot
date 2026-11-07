"""Tests for connectome/analyze_subgraph.py (Phase 3A)."""

import pandas as pd
import pytest

from connectome import analyze_subgraph as an


def edges() -> pd.DataFrame:
    # left giant fiber: LPLC2 with 10, 5, 3, 2 synapses; right: LC4 with 8, 1
    rows = [
        ("left", "LPLC2", 10),
        ("left", "LPLC2", 5),
        ("left", "LPLC2", 3),
        ("left", "LPLC2", 2),
        ("right", "LC4", 8),
        ("right", "LC4", 1),
    ]
    return pd.DataFrame(rows, columns=["post_side", "pre_type", "syn_count"])


def test_top_share_takes_at_least_one_item():
    # strongest 10% of 4 items rounds up to 1 item: 10 of 20 synapses
    assert an.top_share(pd.Series([10, 5, 3, 2])) == pytest.approx(0.5)


def test_top_share_of_empty_total_is_zero():
    assert an.top_share(pd.Series([0, 0])) == 0.0


def test_weight_stats_values():
    stats = an.weight_stats(edges()).set_index(["post_side", "pre_type"])
    left = stats.loc[("left", "LPLC2")]
    assert left.neurons == 4
    assert left.synapses == 20
    assert left["mean"] == 5.0
    assert left["median"] == 4.0
    assert (left["min"], left["max"]) == (2, 10)
    assert left.top10pct_share == pytest.approx(0.5)


def test_threshold_effect_counts_and_percentages():
    sweep = an.threshold_effect(edges(), thresholds=(1, 5)).set_index(["post_side", "min_synapses"])
    assert sweep.loc[("left", 1)].neurons_kept == 4
    assert sweep.loc[("left", 5)].neurons_kept == 2  # the 10- and 5-synapse connections
    assert sweep.loc[("left", 5)].synapses_kept_pct == pytest.approx(75.0)  # 15 of 20
    assert sweep.loc[("right", 5)].neurons_kept == 1
    assert sweep.loc[("right", 5)].synapses_kept_pct == pytest.approx(88.9, abs=0.05)  # 8 of 9


def test_threshold_of_one_keeps_everything():
    sweep = an.threshold_effect(edges(), thresholds=(1,))
    assert (sweep.neurons_kept_pct == 100.0).all()
    assert (sweep.synapses_kept_pct == 100.0).all()
