"""Phase 6.5 / Gate G2: the frozen circuit on held-out stimuli, plus the left/right symmetry check.

Everything is read from configs/prereg.yaml (frozen input gain, held-out seeds, scoring, G2 rule,
symmetry check), all written before this script was first run. Outputs:
  logs/heldout_runs.csv, logs/symmetry_runs.csv, logs/gate_g2_result.json,
  notebooks/figures/heldout_results.png

Run from the project root:   .venv/bin/python -m fly.heldout
"""

from __future__ import annotations

import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from fly import circuit as fc
from sim import stimuli as st

PREREG = Path("configs/prereg.yaml")
OUT = Path("logs")
FIG = Path("notebooks/figures/heldout_results.png")


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson 95% interval for a proportion k / n."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, centre - half), min(1.0, centre + half))


def symmetric_stimulus(seed: int) -> st.Stimulus:
    """A looming stimulus drawn like make_stimulus, but exactly centred left-right (x = 0)."""
    p = st.make_stimulus("looming", seed).params
    return st.make_looming(p["radius_m"], p["speed_mps"], p["impact_s"], 0.0, p["y_m"])


_CIRCUIT = None


def _one(job):
    global _CIRCUIT
    if _CIRCUIT is None:
        _CIRCUIT = fc.load_circuit()
    kind, seed, gain = job
    s = symmetric_stimulus(seed) if kind == "symmetric" else st.make_stimulus(kind, seed)
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
        "gf_left": r.gf_spikes["left"],
        "gf_right": r.gf_spikes["right"],
    }


def run_all(jobs, workers: int = 12) -> pd.DataFrame:
    with ProcessPoolExecutor(workers) as pool:
        return pd.DataFrame(list(pool.map(_one, jobs)))


def score(runs: pd.DataFrame, min_x: float) -> dict:
    loom = runs[runs.kind == "looming"]
    out = {}
    k, n = int(loom.triggered.sum()), len(loom)
    out["hit_rate"] = {"k": k, "n": n, "rate": k / n, "wilson95": wilson(k, n)}
    for kind in ("passing", "receding"):
        d = runs[runs.kind == kind]
        k, n = int(d.triggered.sum()), len(d)
        out[f"false_alarm_{kind}"] = {"k": k, "n": n, "rate": k / n, "wilson95": wilson(k, n)}
    other = runs[runs.kind.isin(["passing", "receding"])]
    k, n = int(other.triggered.sum()), len(other)
    out["false_alarm_all"] = {"k": k, "n": n, "rate": k / n, "wilson95": wilson(k, n)}
    ttc = loom.ttc_at_trigger_s.dropna() * 1000
    out["ttc_at_trigger_ms"] = {
        "median": float(ttc.median()),
        "p10": float(ttc.quantile(0.1)),
        "p90": float(ttc.quantile(0.9)),
        "min": float(ttc.min()),
        "max": float(ttc.max()),
    }
    scored = loom[loom.triggered & (loom.x_m.abs() >= min_x)]
    expected = np.where(scored.x_m < 0, "left", "right")
    k, n = int((scored.side == expected).sum()), len(scored)
    out["side_accuracy"] = {"k": k, "n": n, "rate": k / n if n else None, "wilson95": wilson(k, n)}
    out["head_on_not_scored"] = int((loom.triggered & (loom.x_m.abs() < min_x)).sum())
    return out


def make_figure(runs: pd.DataFrame, sym: pd.DataFrame, path: Path = FIG) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (a, b, c) = plt.subplots(1, 3, figsize=(15, 4.8))
    kinds = ["looming", "passing", "receding"]
    rates = [runs[runs.kind == k].triggered.mean() for k in kinds]
    errs = [
        wilson(int(runs[runs.kind == k].triggered.sum()), (runs.kind == k).sum()) for k in kinds
    ]
    lo = [r - e[0] for r, e in zip(rates, errs, strict=True)]
    hi = [e[1] - r for r, e in zip(rates, errs, strict=True)]
    a.bar(kinds, rates, yerr=[lo, hi], color=["#d62728", "#7f7f7f", "#1f77b4"], capsize=6)
    a.set_ylim(0, 1.05)
    a.set_ylabel("fraction that trigger the giant fiber")
    a.set_title("Held-out: 50 stimuli per kind (95% intervals)")
    ttc = runs[runs.kind == "looming"].ttc_at_trigger_s.dropna() * 1000
    b.hist(ttc, bins=15, color="#d62728")
    b.axvline(ttc.median(), color="k", ls="--")
    b.set_xlabel("time to collision at trigger (ms)")
    b.set_ylabel("looming stimuli")
    b.set_title(f"Warning time, median {ttc.median():.0f} ms")
    trig = sym[sym.triggered]
    counts = [int((trig.side == "left").sum()), int((trig.side == "right").sum())]
    c.bar(["left GF first", "right GF first"], counts, color=["#9467bd", "#8c564b"])
    c.set_title(f"Symmetric head-on looms ({len(trig)} of {len(sym)} triggered)")
    c.set_ylabel("trials")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    print("wrote", path)


def main() -> None:
    fly = yaml.safe_load(PREREG.read_text())["fly"]
    gain = fly["input_gain"]
    cfg = fly["synthetic_calibration"]
    sc = cfg["held_out_scoring"]
    seeds = {k: range(a, b + 1) for k, (a, b) in cfg["held_out_seeds"].items()}
    lo, hi = cfg["symmetry_check"]["seeds"]
    excluded = set(cfg["excluded_seeds"]) | {
        s for a, b in cfg["seeds"].values() for s in range(a, b + 1)
    }
    jobs = [(k, s, gain) for k, ss in seeds.items() for s in ss]
    assert not excluded & {s for _, s, _ in jobs}, (
        "held-out set overlaps calibration or excluded seeds"
    )
    runs = run_all(jobs)
    sym = run_all([("symmetric", s, gain) for s in range(lo, hi + 1)])
    runs.to_csv(OUT / "heldout_runs.csv", index=False)
    sym.to_csv(OUT / "symmetry_runs.csv", index=False)

    result = score(runs, sc["side_scored_only_if_abs_x_m_at_least"])
    trig = sym[sym.triggered]
    right_share = float((trig.side == "right").mean()) if len(trig) else None
    result["symmetry"] = {
        "n": len(sym),
        "triggered": len(trig),
        "right_first_share": right_share,
        "switch_rule_triggered": right_share is not None and not (0.4 <= right_share <= 0.6),
    }
    g2 = (
        result["hit_rate"]["wilson95"][0] >= 0.8 and result["false_alarm_all"]["wilson95"][1] <= 0.2
    )
    result["gate_g2_pass"] = bool(g2)
    result["input_gain"] = gain
    (OUT / "gate_g2_result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    make_figure(runs, sym)


if __name__ == "__main__":
    main()
