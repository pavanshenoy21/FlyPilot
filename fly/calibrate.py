"""Phase 6.2-6.3: tune the one number (input gain) on the calibration set, by the pre-registered rule.

Seeds, gain grid and rule are read from configs/prereg.yaml (fly.synthetic_calibration), which was
written before the first calibration run. Outputs:
  logs/calibration_runs.csv      one row per (gain, stimulus): trigger, side, TTC at trigger
  logs/calibration_result.json   chosen gain and the numbers behind it
  notebooks/figures/calibration_curve.png

Run from the project root:   .venv/bin/python -m fly.calibrate
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
RUNS = Path("logs/calibration_runs.csv")
RESULT = Path("logs/calibration_result.json")
FIG = Path("notebooks/figures/calibration_curve.png")


def settings() -> dict:
    cfg = yaml.safe_load(PREREG.read_text())["fly"]["synthetic_calibration"]
    lo, hi, n = 1.0, 100.0, 25
    assert cfg["gain_grid"] == "geomspace(1, 100, 25)", "gain grid changed in prereg"
    return {
        "seeds": {k: list(range(a, b + 1)) for k, (a, b) in cfg["seeds"].items()},
        "excluded": set(cfg["excluded_seeds"]),
        "grid": np.geomspace(lo, hi, n),
    }


def expected_side(stim: st.Stimulus) -> str | None:
    """Threat side for a looming stimulus: the side the object is on (None if dead centre)."""
    x = stim.params.get("x_m", 0.0)
    return None if abs(x) < 1e-9 else ("left" if x < 0 else "right")


_CIRCUIT = None


def _one(job):
    global _CIRCUIT
    if _CIRCUIT is None:
        _CIRCUIT = fc.load_circuit()
    kind, seed, gains = job
    s = st.make_stimulus(kind, seed)
    rows = []
    for g in gains:
        r = fc.run(_CIRCUIT, s.frames, g)
        trig = None if r.trigger_ms is None else r.trigger_ms / 1000
        ttc = s.ttc_s[0] - trig if (trig is not None and kind == "looming") else np.nan
        rows.append(
            {
                "gain": g,
                "kind": kind,
                "seed": seed,
                "triggered": trig is not None,
                "trigger_s": trig,
                "ttc_at_trigger_s": ttc,
                "side": r.threat_side,
                "expected_side": expected_side(s) if kind == "looming" else None,
                "source_spikes": r.source_spikes,
            }
        )
    return rows


def evaluate(gains: np.ndarray, seeds: dict, workers: int = 12) -> pd.DataFrame:
    jobs = [(k, s, list(gains)) for k, ss in seeds.items() for s in ss]
    with ProcessPoolExecutor(workers) as pool:
        rows = [r for chunk in pool.map(_one, jobs) for r in chunk]
    return pd.DataFrame(rows)


def summarise(runs: pd.DataFrame) -> pd.DataFrame:
    g = runs.groupby("gain")
    loom = runs[runs.kind == "looming"].groupby("gain")
    other = runs[runs.kind != "looming"].groupby("gain")
    out = pd.DataFrame(
        {
            "hits": loom.triggered.sum(),
            "n_looming": loom.size(),
            "false_alarms": other.triggered.sum(),
            "n_other": other.size(),
            "median_ttc_s": loom.ttc_at_trigger_s.median(),
        }
    )
    lr = runs[(runs.kind == "looming") & runs.triggered & runs.expected_side.notna()]
    out["side_correct"] = (lr.side == lr.expected_side).groupby(lr.gain).mean()
    out["score"] = out.hits - out.false_alarms
    return out.reindex(g.size().index)


def choose(summary: pd.DataFrame) -> float:
    """Pre-registered rule: middle of the longest run of grid gains with the maximum score."""
    best = summary.score.max()
    idx = np.flatnonzero(summary.score.to_numpy() == best)
    runs, start = [], 0
    for i in range(1, len(idx) + 1):
        if i == len(idx) or idx[i] != idx[i - 1] + 1:
            runs.append(idx[start:i])
            start = i
    longest = max(runs, key=len)
    return float(summary.index[longest[len(longest) // 2]])


def make_figure(summary: pd.DataFrame, chosen: float, path: Path = FIG) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 5.5))
    gains = summary.index.to_numpy()
    ax.plot(
        gains, summary.hits / summary.n_looming, "o-", color="#d62728", label="looming: hit rate"
    )
    ax.plot(
        gains,
        summary.false_alarms / summary.n_other,
        "s-",
        color="#7f7f7f",
        label="passing + receding: false-alarm rate",
    )
    ax.axvline(chosen, color="k", ls="--", lw=1)
    ax.text(chosen * 1.05, 0.5, f"chosen gain {chosen:.2f}", rotation=90, va="center")
    ax.set_xscale("log")
    ax.set_xlabel("input gain (1 = reference edge brings a neuron to threshold)")
    ax.set_ylabel("fraction of calibration stimuli that trigger")
    ax.set_ylim(-0.05, 1.05)
    ax2 = ax.twinx()
    ax2.plot(
        gains, summary.median_ttc_s * 1000, "^:", color="#1f77b4", label="median TTC at trigger"
    )
    ax2.set_ylabel("median TTC at trigger (ms)", color="#1f77b4")
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper left")
    ax.set_title("Calibration (30 synthetic stimuli): giant-fiber triggering against input gain")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    print("wrote", path)


def main() -> None:
    cfg = settings()
    for seeds in cfg["seeds"].values():
        assert not cfg["excluded"] & set(seeds), "calibration uses an excluded seed"
    runs = evaluate(cfg["grid"], cfg["seeds"])
    runs.to_csv(RUNS, index=False)
    summary = summarise(runs)
    chosen = choose(summary)
    print(summary.round(3).to_string())
    print(f"\nchosen input gain: {chosen:.4f}")
    RESULT.write_text(
        json.dumps(
            {
                "chosen_input_gain": chosen,
                "rule": "middle of the longest run of grid gains with max (hits - false alarms)",
                "at_chosen": {
                    k: (None if pd.isna(v) else float(v))
                    for k, v in summary.loc[chosen].to_dict().items()
                },
                "n_stimuli": int(runs.groupby(["kind", "seed"]).ngroups),
            },
            indent=2,
        )
        + "\n"
    )
    print("wrote", RESULT)
    make_figure(summary, chosen)


if __name__ == "__main__":
    main()
