"""Tests for the per-side input gain (Phase 6.5b, decisions_log 27)."""

import numpy as np

from fly import circuit as fc
from fly import side_gain as sg
from sim import stimuli as st


def test_gains_keep_the_geometric_mean():
    g = sg.gains(5.0, 1.1)
    assert np.isclose(np.sqrt(g["left"] * g["right"]), 5.0) and g["right"] > g["left"]


def test_choose_a_takes_share_closest_to_half_then_closest_to_one():
    assert sg.choose_a({0.9: 0.2, 1.0: 0.375, 1.03: 0.6, 1.05: 0.7}) == 1.03
    assert sg.choose_a({0.95: 0.45, 1.0: 0.6, 1.1: 0.45}) == 0.95  # tie: 0.95 is nearer 1 than 1.1


def test_per_side_drive_scales_each_eye_separately():
    c = fc.load_circuit()
    frames = st.make_looming(0.25, 3.0, 1.5).frames
    one = fc.source_drive(c, frames, 1.0)
    split = fc.source_drive(c, frames, {"left": 2.0, "right": 3.0})
    side = c.side[c.source_idx]
    assert np.allclose(split[:, side == "left"], 2 * one[:, side == "left"])
    assert np.allclose(split[:, side == "right"], 3 * one[:, side == "right"])
