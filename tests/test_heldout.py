"""Tests for fly/heldout.py (Phase 6.5 / Gate G2): intervals, symmetric stimuli, scoring."""

import numpy as np
import pandas as pd
import pytest

from fly import heldout as ho


def test_wilson_interval_known_values():
    lo, hi = ho.wilson(50, 50)
    assert lo == pytest.approx(0.9286, abs=1e-3) and hi == 1.0
    lo, hi = ho.wilson(0, 100)
    assert lo == 0.0 and hi == pytest.approx(0.0370, abs=1e-3)


def test_symmetric_stimulus_is_centred_left_right():
    s = ho.symmetric_stimulus(3000)
    assert s.params["x_m"] == 0.0
    assert np.allclose(s.frames, s.frames[:, :, ::-1], atol=1e-6)  # mirror image of itself


def test_score_counts_and_skips_head_on_sides():
    runs = pd.DataFrame(
        {
            "kind": ["looming"] * 3 + ["passing", "receding"],
            "seed": [1, 2, 3, 1, 1],
            "x_m": [-0.1, 0.1, 0.001, np.nan, np.nan],
            "triggered": [True, True, True, False, True],
            "ttc_at_trigger_s": [0.2, 0.1, 0.15, np.nan, np.nan],
            "side": ["left", "left", "right", None, "left"],
        }
    )
    r = ho.score(runs, min_x=0.02)
    assert r["hit_rate"]["k"] == 3
    assert r["false_alarm_all"]["k"] == 1 and r["false_alarm_receding"]["k"] == 1
    assert (r["side_accuracy"]["k"], r["side_accuracy"]["n"]) == (1, 2)  # third is head-on
    assert r["head_on_not_scored"] == 1
