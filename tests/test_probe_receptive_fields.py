"""Tests for the pure functions in connectome/probe_receptive_fields.py (Phase 3B).

The network reader (HttpFile / fetch_rows) is not tested here: it needs the 9.5 GB remote file.
"""

import numpy as np
import pandas as pd
import pytest

from connectome import probe_receptive_fields as rf


def rows_for(
    neuron: int, neuropil: str, voxels: list[tuple[int, int, int]], batch: int
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "post_pt_root_id": neuron,
            "neuropil": neuropil,
            "post_pt_position_x": [v[0] for v in voxels],
            "post_pt_position_y": [v[1] for v in voxels],
            "post_pt_position_z": [v[2] for v in voxels],
            "batch": batch,
        }
    )


def test_centroid_converts_voxels_to_micrometres():
    # the synapse table stores nanometres: 1000 nm = 1 um
    df = rows_for(1, "LO_L", [(1000, 2000, 100), (3000, 4000, 300)], batch=0)
    c = rf.centroids(df).iloc[0]
    assert c.cx == pytest.approx(2.0)
    assert c.cy == pytest.approx(3.0)
    assert c.cz == pytest.approx(0.2)
    assert c.n_sites == 2


def test_centroids_are_kept_separate_per_layer_and_neuron():
    df = pd.concat(
        [
            rows_for(1, "LO_L", [(0, 0, 0)], 0),
            rows_for(1, "LOP_L", [(4000, 0, 0)], 0),
            rows_for(2, "LO_R", [(8000, 0, 0)], 0),
        ]
    )
    c = rf.centroids(df).set_index(["root_id", "layer"])
    assert set(c.index) == {(1, "LO"), (1, "LOP"), (2, "LO")}
    assert c.loc[(1, "LOP"), "cx"] == pytest.approx(4.0)


def test_min_sites_filters_sparse_neurons():
    df = pd.concat([rows_for(1, "LO_L", [(0, 0, 0)], 0), rows_for(2, "LO_L", [(0, 0, 0)] * 3, 0)])
    assert list(rf.centroids(df, min_sites=2).root_id) == [2]


def test_spread_is_zero_for_identical_sites():
    df = rows_for(1, "LO_L", [(500, 500, 50)] * 4, 0)
    assert rf.centroids(df).iloc[0].spread_um == pytest.approx(0.0)


def test_split_half_is_zero_when_halves_agree():
    rng = np.random.default_rng(0)
    base = rng.integers(0, 5000, size=(40, 3))
    df = pd.concat(
        [rows_for(1, "LO_L", [tuple(p) for p in base[i::2]], batch=b) for i, b in enumerate([0, 1])]
    )
    # both batches contain disjoint points from the same cloud, then duplicate each so the means match exactly
    both = pd.concat([df.assign(batch=0), df.assign(batch=1)])
    out = rf.split_half(both, min_sites=1)
    assert out.half_distance_um.iloc[0] == pytest.approx(0.0, abs=1e-9)


def test_split_half_detects_disagreement():
    a = rows_for(1, "LO_L", [(0, 0, 0)] * 6, batch=0)
    b = rows_for(1, "LO_L", [(5000, 0, 0)] * 6, batch=1)
    out = rf.split_half(pd.concat([a, b]), min_sites=1)
    assert out.half_distance_um.iloc[0] == pytest.approx(5.0)  # 5000 nm
