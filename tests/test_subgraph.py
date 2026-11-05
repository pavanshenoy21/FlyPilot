"""Tests for connectome/build_subgraph.py (Phase 2C).

Most tests use tiny synthetic tables so they run instantly and need no downloaded data.
One test checks the real snapshot-783 numbers and is skipped if the data is not present.
"""

from pathlib import Path

import pandas as pd
import pytest

from connectome import build_subgraph as bs

RAW = Path("connectome/data/raw")
REAL_DATA = (RAW / "proofread_connections_783.feather").exists() and (
    RAW / "Supplemental_file1_neuron_annotations.tsv"
).exists()

# synthetic ids
GF_L, GF_R = 1001, 1002
LP_L1, LP_L2, LP_R1 = 11, 12, 21
LC4_R1 = 22
LP_L_NO_EDGE = 13  # an LPLC2 neuron with no connection to a giant fiber
OTHER = 99  # not an LPLC2/LC4 neuron
GABA_SRC = 31  # an LC4 neuron predicted GABA, no known transmitter (used to test sign)
KNOWN_SRC = 41  # an LC4 neuron predicted GABA but experimentally known to be acetylcholine


def annotations() -> pd.DataFrame:
    rows = [
        (GF_L, "DNp01", "Giant Fiber", "left", "acetylcholine"),
        (GF_R, "DNp01", "Giant Fiber", "right", "glutamate"),
        (LP_L1, "LPLC2", "LPLC2", "left", "acetylcholine"),
        (LP_L2, "LPLC2", "LPLC2", "left", "acetylcholine"),
        (LP_R1, "LPLC2", "LPLC2", "right", "acetylcholine"),
        (LC4_R1, "LC4", "LC4", "right", "acetylcholine"),
        (LP_L_NO_EDGE, "LPLC2", "LPLC2", "left", "acetylcholine"),
        (GABA_SRC, "LC4", "LC4", "left", "gaba"),
        (KNOWN_SRC, "LC4", "LC4", "left", "gaba"),
        (OTHER, "CB3707", "CB3707", "left", "acetylcholine"),
    ]
    df = pd.DataFrame(rows, columns=["root_id", "cell_type", "hemibrain_type", "side", "top_nt"])
    df["top_nt_conf"] = 0.9
    df["known_nt"] = None
    df["known_nt_source"] = None
    df.loc[df.root_id == KNOWN_SRC, "known_nt"] = "acetylcholine"
    df.loc[df.root_id == KNOWN_SRC, "known_nt_source"] = "test"
    for c in ("pos_x", "pos_y", "pos_z", "soma_x", "soma_y", "soma_z"):
        df[c] = 0
    return df


def conn_row(pre, post, neuropil, syn, ach=1.0, gaba=0.0):
    return {
        "pre_pt_root_id": pre,
        "post_pt_root_id": post,
        "neuropil": neuropil,
        "syn_count": syn,
        "ach_avg": ach,
        "gaba_avg": gaba,
        "glut_avg": 0.0,
        "oct_avg": 0.0,
        "ser_avg": 0.0,
        "da_avg": 0.0,
    }


def connections() -> pd.DataFrame:
    return pd.DataFrame(
        [
            conn_row(LP_L1, GF_L, "LOP_L", 3),
            conn_row(LP_L1, GF_L, "LO_L", 2),  # same pair, second neuropil -> must be summed
            conn_row(LP_L2, GF_L, "LOP_L", 4),
            conn_row(LP_R1, GF_R, "LOP_R", 5),
            conn_row(LC4_R1, GF_R, "LO_R", 6),
            conn_row(GABA_SRC, GF_L, "LO_L", 7, ach=0.0, gaba=1.0),
            conn_row(KNOWN_SRC, GF_L, "LO_L", 8, ach=0.0, gaba=1.0),
            conn_row(OTHER, GF_L, "LOP_L", 50),  # not a source type -> excluded
            conn_row(LP_L1, OTHER, "LOP_L", 40),  # target is not a giant fiber -> excluded
        ]
    )


def build():
    return bs.build_subgraph(annotations(), connections())


def test_neuropil_rows_are_summed_into_one_edge():
    _, edges, _ = build()
    e = edges[(edges.pre_root_id == LP_L1) & (edges.post_root_id == GF_L)]
    assert len(e) == 1
    assert int(e.syn_count.iloc[0]) == 5
    assert int(e.n_neuropils.iloc[0]) == 2


def test_only_source_types_into_giant_fibers_are_kept():
    _, edges, _ = build()
    assert set(edges.pre_root_id) == {LP_L1, LP_L2, LP_R1, LC4_R1, GABA_SRC, KNOWN_SRC}
    assert set(edges.post_root_id) == {GF_L, GF_R}
    assert OTHER not in set(edges.pre_root_id)


def test_sources_without_an_edge_are_not_nodes_but_are_counted():
    nodes, _, summary = build()
    assert LP_L_NO_EDGE not in set(nodes.root_id)
    assert summary["sources"]["LPLC2_left"]["neurons_without_edge"] == 1
    assert summary["sources"]["LPLC2_left"]["neurons_with_direct_edge_to_gf"] == 2


def test_both_giant_fibers_are_always_nodes():
    nodes, _, _ = build()
    assert set(nodes[nodes.role == "giant_fiber"].root_id) == {GF_L, GF_R}


def test_sign_follows_locked_transmitter_rule():
    _, edges, _ = build()
    sign = edges.set_index("pre_root_id").sign
    assert sign[LP_L1] == 1  # acetylcholine -> excitatory
    assert sign[GABA_SRC] == -1  # gaba -> inhibitory


def test_known_transmitter_overrides_prediction_and_is_flagged():
    _, edges, summary = build()
    by = edges.set_index("pre_root_id")
    assert by.loc[KNOWN_SRC, "sign"] == 1  # known acetylcholine wins over predicted gaba
    assert by.loc[KNOWN_SRC, "nt_source"] == "known"
    assert by.loc[GABA_SRC, "sign"] == -1  # no known transmitter -> prediction is used
    assert by.loc[GABA_SRC, "nt_source"] == "predicted"
    assert summary["edges_by_sign_source"] == {"predicted": 5, "known": 1}


@pytest.mark.parametrize(
    ("nt", "expected"),
    [
        ("acetylcholine", 1),
        ("ACETYLCHOLINE", 1),
        ("gaba", -1),
        ("glutamate", -1),
        ("dopamine", 0),
        ("serotonin", 0),
        ("octopamine", 0),
        (None, 0),
        (float("nan"), 0),
    ],
)
def test_nt_sign(nt, expected):
    assert bs.nt_sign(nt) == expected


def test_same_side_fraction_is_reported():
    _, edges, summary = build()
    assert edges.same_side.all()
    assert summary["same_side_fraction_by_synapse"] == 1.0


def test_building_twice_gives_identical_output():
    n1, e1, s1 = build()
    n2, e2, s2 = build()
    pd.testing.assert_frame_equal(n1, n2)
    pd.testing.assert_frame_equal(e1, e2)
    assert s1 == s2


def test_missing_giant_fiber_side_raises():
    ann = annotations()
    ann = ann[ann.root_id != GF_R]
    with pytest.raises(ValueError, match="one left and one right"):
        bs.select_giant_fibers(ann)


@pytest.mark.skipif(not REAL_DATA, reason="FlyWire snapshot 783 not downloaded")
def test_real_snapshot_reproduces_phase_2b_numbers():
    ann = bs.load_annotations(RAW / "Supplemental_file1_neuron_annotations.tsv")
    gf = bs.select_giant_fibers(ann)
    conn = bs.read_connections_into(RAW / "proofread_connections_783.feather", gf.root_id.tolist())
    _, edges, summary = bs.build_subgraph(ann, conn)

    def count(side, cell_type):
        sel = edges[(edges.post_side == side) & (edges.pre_type == cell_type)]
        return len(sel), int(sel.syn_count.sum())

    assert count("right", "LPLC2") == (95, 622)
    assert count("right", "LC4") == (50, 431)
    assert count("left", "LPLC2") == (94, 458)
    assert count("left", "LC4") == (54, 374)
    assert summary["same_side_fraction_by_synapse"] == 1.0
