"""Phase 7.2: the 20 shuffled circuits through the real circuit's own tuning procedure.

Procedure (configs/prereg.yaml shuffle.synthetic_check, written before this was first run):
  1. input gain: calibration seeds x gain grid, pre-registered rule (fly/calibrate.py)
  2. symmetry check at that gain; only if right-first share is outside 0.4-0.6, per-side split
     tuned on seeds 4000-4039 with the same grid and rule (fly/side_gain.py)
  3. held-out set and symmetry seeds at the final gains
  secondary: held-out set at the real circuit's frozen gains
The real circuit's values come from logs/side_gain_result.json. Outputs:
  logs/shuffle_calibration_runs.csv, logs/shuffle_heldout_runs.csv, logs/shuffle_per_seed.csv,
  logs/shuffle_result.json

Run from the project root:   .venv/bin/python -m fly.shuffle_eval
"""

from __future__ import annotations

import json
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from fly import calibrate as cal
from fly import circuit as fc
from fly import heldout as ho
from fly import shuffle as sh
from fly import side_gain as sg
from sim import stimuli as st

PREREG = Path("configs/prereg.yaml")
LOGS = Path("logs")
# metric name -> (path in the score() dict, higher is better)
METRICS = {
    "median_ttc_at_trigger_ms": (("ttc_at_trigger_ms", "median"), True),
    "side_accuracy": (("side_accuracy", "rate"), True),
    "hit_rate": (("hit_rate", "rate"), True),
    "false_alarm_rate": (("false_alarm_all", "rate"), False),
}

_CACHE: dict = {}


def _circuit(wseed: int) -> fc.Circuit:
    if wseed not in _CACHE:
        base = _CACHE.setdefault("base", fc.load_circuit())
        _CACHE[wseed] = sh.shuffled_circuit(wseed, base)
    return _CACHE[wseed]


def _job(job) -> list[dict]:
    """One stimulus through one shuffled circuit at several gains: (wseed, kind, seed, [(label, gain)])."""
    wseed, kind, seed, gains = job
    c = _circuit(wseed)
    s = ho.symmetric_stimulus(seed) if kind == "symmetric" else st.make_stimulus(kind, seed)
    looming = kind in ("looming", "symmetric")
    rows = []
    for label, g in gains:
        r = fc.run(c, s.frames, g)
        trig = None if r.trigger_ms is None else r.trigger_ms / 1000
        rows.append(
            {
                "wiring_seed": wseed,
                "gain": label,
                "kind": kind,
                "seed": seed,
                "x_m": s.params.get("x_m", np.nan),
                "triggered": trig is not None,
                "trigger_s": trig,
                "ttc_at_trigger_s": s.ttc_s[0] - trig if (trig is not None and looming) else np.nan,
                "side": r.threat_side,
                "expected_side": cal.expected_side(s) if kind == "looming" else None,
            }
        )
    return rows


def run_jobs(jobs, workers: int = 12) -> pd.DataFrame:
    with ProcessPoolExecutor(workers) as pool:
        return pd.DataFrame([r for rows in pool.map(_job, jobs, chunksize=1) for r in rows])


def compare(real: float, shuffled: list[float], higher_better: bool) -> dict:
    """Real circuit against the shuffled distribution (prereg shuffle.synthetic_check)."""
    v = np.asarray(shuffled, dtype=float)
    better = v < real if higher_better else v > real
    at_least_as_good = v >= real if higher_better else v <= real
    return {
        "real": real,
        "shuffled_mean": float(v.mean()),
        "shuffled_sd": float(v.std(ddof=1)) if len(v) > 1 else 0.0,
        "shuffled_min": float(v.min()),
        "shuffled_max": float(v.max()),
        "real_beats_share": float((better.sum() + 0.5 * (v == real).sum()) / len(v)),
        "p_one_sided": float((1 + at_least_as_good.sum()) / (1 + len(v))),
    }


def metric(score: dict, name: str) -> float:
    (a, b), _ = METRICS[name]
    x = score[a][b]
    return float("nan") if x is None else float(x)


def main(wseeds=None, workers: int = 12) -> dict:
    prereg = yaml.safe_load(PREREG.read_text())
    fly, shuf = prereg["fly"], prereg["shuffle"]
    cfg = fly["synthetic_calibration"]
    psg = cfg["per_side_gain"]
    if wseeds is None:
        lo, hi = shuf["wiring_seeds"]
        wseeds = range(lo, hi + 1)
    wseeds = list(wseeds)
    sets = cal.settings()
    grid = sets["grid"]
    assert psg["a_grid"] == "geomspace(1/1.3, 1.3, 21)"
    a_grid = np.geomspace(1 / 1.3, 1.3, 21)
    rng = lambda pair: range(pair[0], pair[1] + 1)
    sym_seeds, tune_seeds = rng(cfg["symmetry_check"]["seeds"]), rng(psg["tuning_seeds"])
    held = {k: rng(v) for k, v in cfg["held_out_seeds"].items()}
    min_x = cfg["held_out_scoring"]["side_scored_only_if_abs_x_m_at_least"]
    frozen = {"left": psg["left_gain"], "right": psg["right_gain"]}
    t0 = time.time()

    # 1. input gain, by the calibration rule
    calib = run_jobs(
        [
            (w, k, s, [(float(g), float(g)) for g in grid])
            for w in wseeds
            for k, ss in sets["seeds"].items()
            for s in ss
        ],
        workers,
    )
    calib.to_csv(LOGS / "shuffle_calibration_runs.csv", index=False)
    gain = {w: cal.choose(cal.summarise(calib[calib.wiring_seed == w])) for w in wseeds}
    print(f"1. gains chosen ({time.time() - t0:.0f} s):", {w: round(g, 3) for w, g in gain.items()})

    # 2. symmetry check; per-side split only where the rule fires
    sym = run_jobs(
        [(w, "symmetric", s, [("single", gain[w])]) for w in wseeds for s in sym_seeds], workers
    )
    share = {w: sg.right_share(sym[sym.wiring_seed == w]) for w in wseeds}
    needs = [w for w in wseeds if not (0.4 <= share[w] <= 0.6)]
    print(f"2. symmetry ({time.time() - t0:.0f} s): split needed for {len(needs)} of {len(wseeds)}")
    a = {w: 1.0 for w in wseeds}
    if needs:
        tune = run_jobs(
            [
                (w, "symmetric", s, [(float(x), sg.gains(gain[w], x)) for x in a_grid])
                for w in needs
                for s in tune_seeds
            ],
            workers,
        )
        for w in needs:
            d = tune[tune.wiring_seed == w]
            a[w] = sg.choose_a({float(x): sg.right_share(d[d.gain == float(x)]) for x in a_grid})
    final = {w: sg.gains(gain[w], a[w]) for w in wseeds}
    print(f"3. split tuned ({time.time() - t0:.0f} s):", {w: round(a[w], 4) for w in needs})

    # 3. held-out at the final gains (+ symmetry re-run where split), and at the real frozen gains
    jobs = [
        (w, k, s, [("tuned", final[w]), ("real_frozen", frozen)])
        for w in wseeds
        for k, ss in held.items()
        for s in ss
    ]
    jobs += [(w, "symmetric", s, [("tuned", final[w])]) for w in needs for s in sym_seeds]
    test = run_jobs(jobs, workers)
    test.to_csv(LOGS / "shuffle_heldout_runs.csv", index=False)
    print(f"4. held-out done ({time.time() - t0:.0f} s)")

    real_score = json.loads((LOGS / "side_gain_result.json").read_text())["recheck_heldout"]
    rows, scores = [], {"tuned": {}, "real_frozen": {}}
    for w in wseeds:
        d = test[test.wiring_seed == w]
        s_sym = sym[sym.wiring_seed == w] if w not in needs else d[(d.kind == "symmetric")]
        for label, by_seed in scores.items():
            dl = d[(d.gain == label) & (d.kind != "symmetric")]
            by_seed[w] = ho.score(dl, min_x)
        rows.append(
            {
                "wiring_seed": w,
                "input_gain": gain[w],
                "a": a[w],
                "left_gain": final[w]["left"],
                "right_gain": final[w]["right"],
                "symmetry_right_share_single_gain": share[w],
                "symmetry_right_share_final": sg.right_share(s_sym),
                **{f"tuned_{m}": metric(scores["tuned"][w], m) for m in METRICS},
                **{f"real_frozen_{m}": metric(scores["real_frozen"][w], m) for m in METRICS},
            }
        )
    per_seed = pd.DataFrame(rows)
    per_seed.to_csv(LOGS / "shuffle_per_seed.csv", index=False)

    result = {"n_shuffles": len(wseeds), "wiring_seeds": wseeds, "runtime_s": time.time() - t0}
    for label in scores:
        result[label] = {
            m: compare(metric(real_score, m), [metric(scores[label][w], m) for w in wseeds], hb)
            for m, (_, hb) in METRICS.items()
        }
    (LOGS / "shuffle_result.json").write_text(json.dumps(result, indent=2) + "\n")
    with pd.option_context("display.width", 200, "display.max_columns", 30):
        print(per_seed.round(3).to_string(index=False))
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
