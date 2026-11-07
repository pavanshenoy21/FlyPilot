"""Tests for connectome/asymmetry_check.py (Phase 3C), on tiny synthetic tables."""

import pandas as pd

from connectome import asymmetry_check as ac

GF_L, GF_R = 1001, 1002
LP_L, LP_R, LC4_L, OTHER = 11, 21, 31, 99


def ann() -> pd.DataFrame:
    rows = [
        (GF_L, "DNp01", "Giant Fiber", "left"),
        (GF_R, "DNp01", "Giant Fiber", "right"),
        (LP_L, "LPLC2", "LPLC2", "left"),
        (LP_R, "LPLC2", "LPLC2", "right"),
        (LC4_L, "LC4", "LC4", "left"),
        (OTHER, "CB3707", "CB3707", "left"),
    ]
    return pd.DataFrame(rows, columns=["root_id", "cell_type", "hemibrain_type", "side"])


def conn() -> pd.DataFrame:
    rows = [
        (LP_L, GF_L, 4),
        (LC4_L, GF_L, 2),
        (OTHER, GF_L, 10),
        (LP_R, GF_R, 6),
        (OTHER, GF_R, 14),
        (GF_L, OTHER, 3),  # output of a giant fiber, not an input: must be ignored
        (OTHER, LP_L, 7),  # an input to a source neuron (counts for completeness only)
        (LP_L, OTHER, 5),  # an output of a source neuron
    ]
    return pd.DataFrame(rows, columns=["pre_pt_root_id", "post_pt_root_id", "syn_count"])


def test_gf_input_split_by_kind_and_side():
    t = ac.gf_input_by_kind(conn(), ann())
    assert t.loc["LPLC2", "left"] == 4 and t.loc["LPLC2", "right"] == 6
    assert t.loc["LC4", "left"] == 2 and t.loc["LC4", "right"] == 0
    assert t.loc["other", "left"] == 10 and t.loc["other", "right"] == 14


def test_right_over_left_ratio():
    t = ac.gf_input_by_kind(conn(), ann())
    assert t.loc["LPLC2", "right_over_left"] == 1.5  # 6 / 4
    assert t.loc["other", "right_over_left"] == 1.4  # 14 / 10


def test_source_completeness_counts_inputs_and_outputs():
    t = ac.source_completeness(conn(), ann())
    left = t.loc[("LPLC2", "left")]
    assert left.input_synapses == 7  # OTHER -> LP_L
    assert left.output_synapses == 9  # 4 to the giant fiber + 5 to OTHER
