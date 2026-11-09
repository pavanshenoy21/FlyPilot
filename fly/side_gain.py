"""Phase 6.5b: one input gain per side, as the pre-registered symmetry rule requires (decisions_log 27).

left = g / a, right = g * a, with g the frozen input gain. a is chosen on fresh centred looms
(seeds in prereg fly.synthetic_calibration.per_side_gain) so that each giant fiber fires first half
the time. Then the symmetry seeds and the held-out set are re-checked (reported, not tuned on).

Run from the project root:   .venv/bin/python -m fly.side_gain
"""

from __future__ import annotations

import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from fly import circuit as fc
from fly import heldout as ho
from sim import stimuli as st

PREREG = Path("configs/prereg.yaml")
OUT = Path("logs/side_gain_result.json")

_CIRCUIT = None


def gains(g: float, a: float) -> dict:
    return {"left": g / a, "right": g * a}


def _first(job):
    global _CIRCUIT
    if _CIRCUIT is None:
        _CIRCUIT = fc.load_circuit()
    kind, seed, gain = job
    s = ho.symmetric_stimulus(seed) if kind == "symmetric" else st.make_stimulus(kind, seed)
    r = fc.run(_CIRCUIT, s.frames, gain)
    trig = None if r.trigger_ms is None else r.trigger_ms / 1000
    looming = kind in ("looming", "symmetric")
    return {
        "kind": kind,
        "seed": seed,
        "x_m": s.params.get("x_m", np.nan),
        "triggered": trig is not None,
        "trigger_s": trig,
        "ttc_at_trigger_s": s.ttc_s[0] - trig if (trig is not None and looming) else np.nan,
        "side": r.threat_side,
    }


def run_jobs(jobs, workers: int = 12) -> pd.DataFrame:
    with ProcessPoolExecutor(workers) as pool:
        return pd.DataFrame(list(pool.map(_first, jobs)))


def right_share(df: pd.DataFrame) -> float:
    t = df[df.triggered]
    return float((t.side == "right").mean())


def choose_a(shares: dict) -> float:
    """Pre-registered: share closest to 0.5; ties -> a closest to 1 (in log terms)."""
    return min(shares, key=lambda a: (round(abs(shares[a] - 0.5), 9), abs(np.log(a))))


def main() -> None:
    fly = yaml.safe_load(PREREG.read_text())["fly"]
    g = fly["input_gain"]
    cfg = fly["synthetic_calibration"]
    psg = cfg["per_side_gain"]
    assert psg["a_grid"] == "geomspace(1/1.3, 1.3, 21)"
    grid = np.geomspace(1 / 1.3, 1.3, 21)
    lo, hi = psg["tuning_seeds"]
    tune_seeds = range(lo, hi + 1)
    shares = {}
    for a in grid:
        df = run_jobs([("symmetric", s, gains(g, a)) for s in tune_seeds])
        shares[float(a)] = right_share(df)
        print(
            f"a = {a:.4f}: right first {shares[float(a)]:.3f} ({df.triggered.sum()}/40 triggered)"
        )
    a = choose_a(shares)
    chosen = gains(g, a)
    print(f"\nchosen a = {a:.4f}: left gain {chosen['left']:.4f}, right gain {chosen['right']:.4f}")

    s_lo, s_hi = cfg["symmetry_check"]["seeds"]
    sym = run_jobs([("symmetric", s, chosen) for s in range(s_lo, s_hi + 1)])
    held = {k: range(a0, b0 + 1) for k, (a0, b0) in cfg["held_out_seeds"].items()}
    runs = run_jobs([(k, s, chosen) for k, ss in held.items() for s in ss])
    sym.to_csv("logs/side_gain_symmetry_runs.csv", index=False)
    runs.to_csv("logs/side_gain_heldout_runs.csv", index=False)
    k = int((sym[sym.triggered].side == "right").sum())
    n = int(sym.triggered.sum())
    result = {
        "a": a,
        "gains": chosen,
        "tuning_right_share_by_a": shares,
        "recheck_symmetry": {
            "right_first": k,
            "triggered": n,
            "share": k / n,
            "wilson95": ho.wilson(k, n),
        },
        "recheck_heldout": ho.score(
            runs, cfg["held_out_scoring"]["side_scored_only_if_abs_x_m_at_least"]
        ),
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps({k2: v for k2, v in result.items() if k2 != "tuning_right_share_by_a"}, indent=2)
    )


if __name__ == "__main__":
    main()
