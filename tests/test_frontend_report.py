"""Tests for fly/frontend_report.py (Phase 5.5): the expansion summary separates the three kinds."""

import numpy as np

from fly.frontend import GRID, coarse_grid, reichardt
from fly.frontend_report import summarise
from sim import stimuli as st


def peak(kind: str, seed: int) -> float:
    s = st.make_stimulus(kind, seed)
    return summarise(reichardt(coarse_grid(s.frames)))[1].max()


def test_expansion_counts_outward_motion_positive():
    m = np.zeros((1, 2, 4, GRID, GRID))
    m[0, 0, 0, :, GRID - 1] = 1.0  # rightward motion on the right edge = outward
    total, expansion = summarise(m)
    assert total[0] == GRID and expansion[0] == GRID
    m[0, 0, 0] = 0
    m[0, 0, 0, :, 0] = 1.0  # rightward on the left edge = inward
    assert summarise(m)[1][0] == -GRID


def test_looming_expands_far_more_than_passing_or_receding():
    looming = [peak("looming", s) for s in range(5)]
    others = [peak(k, s) for k in ("passing", "receding") for s in range(5)]
    assert min(looming) > 10 * max(others)
