"""Tests for fly/shuffle.py (Phase 7.1, Gate G3): the shuffle changes only who connects to whom."""

import numpy as np
import pandas as pd
import pytest

from fly import circuit as fc
from fly import shuffle as sh

EDGES = fc.DATA / "edges.csv"


@pytest.fixture(scope="module")
def real():
    return pd.read_csv(EDGES)


@pytest.mark.parametrize("seed", range(20))
def test_every_preserved_property_holds_for_all_20_seeds(real, seed):
    checks = sh.preserved(real, sh.rewire(real, seed))
    assert all(checks.values()), {k: v for k, v in checks.items() if not v}


def test_wiring_actually_changes_and_depends_on_seed(real):
    a, b = sh.rewire(real, 0), sh.rewire(real, 1)
    assert (a.post_root_id != real.post_root_id).any()
    assert (a.post_root_id != b.post_root_id).any()
    assert a.equals(sh.rewire(real, 0))  # reproducible


def test_preserved_detects_a_broken_shuffle(real):
    broken = real.copy()
    broken.loc[0, "post_root_id"] = broken.post_root_id[
        broken.post_root_id != broken.post_root_id[0]
    ].iloc[0]
    checks = sh.preserved(real, broken)
    assert not checks["in_degree"]
    heavier = real.copy()
    heavier.loc[0, "syn_count"] += 1
    assert not sh.preserved(real, heavier)["total_synapses"]


def test_real_circuit_is_all_same_side_and_shuffles_are_mixed(real):
    assert sh.describe(real)["same_side_edges"] == 1.0
    shares = [sh.describe(sh.rewire(real, s))["same_side_edges"] for s in range(20)]
    assert 0.35 < np.mean(shares) < 0.65


def test_rejects_duplicates_and_self_edges_on_a_dense_toy_graph():
    # 3 nodes, out-degree 2 each: many permutations create duplicates or self-edges
    toy = pd.DataFrame(
        {
            "pre_root_id": [1, 1, 2, 2, 3, 3],
            "post_root_id": [2, 3, 1, 3, 1, 2],
            "syn_count": [1, 2, 3, 4, 5, 6],
            "nt_neuron": ["acetylcholine"] * 6,
        }
    )
    for s in range(10):
        checks = sh.preserved(toy, sh.rewire(toy, s))
        assert checks["no_duplicates"] and checks["no_self_edges"] and checks["in_degree"]


def test_shuffled_circuit_changes_only_the_weights():
    base = fc.load_circuit()
    c = sh.shuffled_circuit(3, base)
    assert c.node_ids == base.node_ids and c.unit_gain_mV == base.unit_gain_mV
    assert np.array_equal(c.kernels, base.kernels)
    assert c.counts.sum() == base.counts.sum() == 1885
    # each source keeps its output synapses; each giant fiber keeps its number of inputs
    assert np.array_equal(c.counts.sum(axis=0), base.counts.sum(axis=0))
    assert np.array_equal((c.counts > 0).sum(axis=1), (base.counts > 0).sum(axis=1))
    assert not np.array_equal(c.counts, base.counts)
