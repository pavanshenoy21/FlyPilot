"""Tests for fly/shuffle_eval.py (Phase 7.2): ranking the real circuit among the shuffles."""

import numpy as np
import pytest

from fly import shuffle_eval as se


def test_compare_counts_ties_as_half_and_gives_permutation_p():
    c = se.compare(10.0, [5.0, 10.0, 12.0, 8.0], higher_better=True)
    assert c["real_beats_share"] == pytest.approx((2 + 0.5) / 4)
    assert c["p_one_sided"] == pytest.approx((1 + 2) / 5)  # 10 and 12 are at least as good
    assert c["shuffled_min"] == 5.0 and c["shuffled_max"] == 12.0


def test_compare_lower_is_better_for_false_alarms():
    c = se.compare(0.0, [0.0, 0.1, 0.2], higher_better=False)
    assert c["real_beats_share"] == pytest.approx((2 + 0.5) / 3)
    assert c["p_one_sided"] == pytest.approx((1 + 1) / 4)


def test_real_circuit_beating_every_shuffle_gives_smallest_p():
    c = se.compare(1.0, list(np.linspace(0, 0.9, 20)), higher_better=True)
    assert c["real_beats_share"] == 1.0 and c["p_one_sided"] == pytest.approx(1 / 21)


def test_job_runs_a_shuffled_circuit_at_several_gains():
    rows = se._job((0, "receding", 2000, [("a", 5.0), ("b", {"left": 5.0, "right": 6.0})]))
    assert [r["gain"] for r in rows] == ["a", "b"]
    assert all(r["wiring_seed"] == 0 and r["kind"] == "receding" for r in rows)
