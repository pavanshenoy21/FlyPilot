"""Phase 5.5: run the three stimulus types through the fixed front end, save summaries and a figure.

For every stimulus: coarse grid -> Reichardt ON/OFF motion energy. Two summaries per frame:
  total   = all motion energy (any direction, both polarities)
  expansion = outward minus inward motion relative to the image centre
            (rightward on the right half + leftward on the left half + downward on the lower half
             + upward on the upper half, minus the opposite directions)
"expansion" is only a preview of what LPLC2 will see; LPLC2 measures outward motion around its own
receptive-field centre, which is wired in Phase 6.

Run from the project root:   .venv/bin/python -m fly.frontend_report
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from fly.frontend import GRID, coarse_grid, reichardt
from sim import stimuli as st

SEEDS = range(5)
CSV = Path("logs/frontend_responses.csv")
FIG = Path("notebooks/figures/frontend_responses.png")
ARROW_UNIT = 0.02  # motion energy drawn as an arrow one grid cell long


def summarise(motion: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """motion [T, 2, 4, n, n] -> (total [T], expansion [T])."""
    m = motion.sum(axis=1)  # both polarities: [T, 4 directions, n, n]
    h = GRID // 2
    right, left, down, up = m[:, 0], m[:, 1], m[:, 2], m[:, 3]
    outward = (
        right[:, :, h:].sum((1, 2))
        + left[:, :, :h].sum((1, 2))
        + down[:, h:, :].sum((1, 2))
        + up[:, :h, :].sum((1, 2))
    )
    inward = (
        left[:, :, h:].sum((1, 2))
        + right[:, :, :h].sum((1, 2))
        + up[:, h:, :].sum((1, 2))
        + down[:, :h, :].sum((1, 2))
    )
    return m.sum(axis=(1, 2, 3)), outward - inward


def run() -> pd.DataFrame:
    rows = []
    for kind in st.KINDS:
        for seed in SEEDS:
            s = st.make_stimulus(kind, seed)
            total, expansion = summarise(reichardt(coarse_grid(s.frames)))
            for k in range(len(s.times_s)):
                rows.append((kind, seed, k, s.times_s[k], s.ttc_s[k], total[k], expansion[k]))
    cols = ["kind", "seed", "frame", "time_s", "ttc_s", "total", "expansion"]
    return pd.DataFrame(rows, columns=cols)


def make_figure(df: pd.DataFrame, path: Path = FIG) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(3, 4, figsize=(14, 10), gridspec_kw={"width_ratios": [1, 1, 1, 1.6]})
    colours = {"looming": "#d62728", "passing": "#7f7f7f", "receding": "#1f77b4"}
    yy, xx = np.mgrid[0:GRID, 0:GRID] + 0.5
    for row, kind in zip(axes, st.KINDS, strict=True):
        s = st.make_stimulus(kind, 1)
        g = coarse_grid(s.frames)
        m = reichardt(g).sum(axis=1)  # [T, 4, n, n]
        picks = np.linspace(len(g) * 0.3, len(g) - 2, 3).astype(int)
        for ax, i in zip(row[:3], picks, strict=True):
            ax.imshow(g[i], cmap="gray", vmin=0, vmax=1, extent=(0, GRID, GRID, 0))
            u = m[i, 0] - m[i, 1]  # net rightward
            v = m[i, 2] - m[i, 3]  # net downward
            u, v = (
                np.ma.masked_where(np.hypot(u, v) < 1e-4, u),
                np.ma.masked_where(np.hypot(u, v) < 1e-4, v),
            )
            # one fixed scale for the whole figure: an arrow of 1 cell = ARROW_UNIT of energy
            ax.quiver(
                xx,
                yy,
                u,
                v,
                color="#ff7f0e",
                angles="xy",
                scale_units="xy",
                scale=ARROW_UNIT,
                pivot="mid",
                width=0.012,
            )
            ax.set_xticks([])
            ax.set_yticks([])
            ttc = s.ttc_s[i]
            ax.set_title(f"t={s.times_s[i]:.2f}s" + ("" if np.isnan(ttc) else f", TTC={ttc:.2f}s"))
        row[0].set_ylabel(kind, fontsize=13)
        ax = row[3]
        for kind2 in st.KINDS:
            for _, d in df[df.kind == kind2].groupby("seed"):
                ax.plot(
                    d.time_s,
                    d.expansion,
                    color=colours[kind2],
                    alpha=0.8 if kind2 == kind else 0.12,
                )
        ax.axhline(0, color="k", lw=0.8)
        ax.set_xlabel("time (s)")
        ax.set_ylabel("expansion (outward - inward)")
        ax.set_title(f"{kind}: 5 random stimuli (bold), others faint")
    fig.suptitle(
        "Front end on the 12 x 12 grid: net motion arrows (orange) and the expansion signal",
        fontsize=14,
    )
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    print("wrote", path)


def main() -> None:
    df = run()
    CSV.parent.mkdir(exist_ok=True)
    df.to_csv(CSV, index=False)
    print("wrote", CSV)
    per = df.groupby(["kind", "seed"]).agg(
        peak_expansion=("expansion", "max"),
        min_expansion=("expansion", "min"),
        mean_expansion=("expansion", "mean"),
        peak_total=("total", "max"),
    )
    print(per.round(3).to_string())
    make_figure(df)


if __name__ == "__main__":
    main()
