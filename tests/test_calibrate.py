"""Tests for fly/calibrate.py (Phase 6.3): the pre-registered rule for choosing the input gain."""

import numpy as np
import pandas as pd

from fly import calibrate as cal


def table(scores):
    gains = np.geomspace(1, 100, len(scores))
    return pd.DataFrame({"score": scores}, index=pd.Index(gains, name="gain"))


def test_rule_picks_the_middle_of_the_best_plateau():
    t = table([0, 5, 10, 10, 10, 10, 10, 9, 8])
    assert cal.choose(t) == t.index[4]  # plateau is positions 2..6, middle is 4


def test_rule_prefers_the_longest_run_when_the_best_score_appears_twice():
    t = table([10, 3, 10, 10, 10, 2])
    assert cal.choose(t) == t.index[3]


def test_settings_match_prereg_and_avoid_excluded_seeds():
    cfg = cal.settings()
    assert len(cfg["grid"]) == 25 and cfg["grid"][0] == 1 and cfg["grid"][-1] == 100
    assert sum(len(s) for s in cfg["seeds"].values()) == 30
    for seeds in cfg["seeds"].values():
        assert not cfg["excluded"] & set(seeds)


def test_summary_counts_hits_and_false_alarms():
    runs = pd.DataFrame(
        {
            "gain": [1.0] * 4,
            "kind": ["looming", "looming", "passing", "receding"],
            "seed": [1, 2, 1, 1],
            "triggered": [True, False, True, False],
            "ttc_at_trigger_s": [0.2, np.nan, np.nan, np.nan],
            "side": ["left", None, "left", None],
            "expected_side": ["left", "right", None, None],
        }
    )
    s = cal.summarise(runs).loc[1.0]
    assert (s.hits, s.false_alarms, s.score) == (1, 1, 0)
    assert s.side_correct == 1.0
