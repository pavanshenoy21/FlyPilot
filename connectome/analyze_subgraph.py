"""Phase 3A: how strong are the connections in the LPLC2 / LC4 -> giant fiber subgraph?

Questions answered:
  * How many synapses does each source neuron contribute (mean, median, min, max)?
  * How concentrated is the input: what share of synapses sit in the strongest 10% of neurons?
  * What happens to the circuit if weak connections are dropped (threshold sweep)?

Reads connectome/data/subgraph_v783/edges.csv (made by build_subgraph.py).
Writes connectome/data/subgraph_v783/analysis.json and notebooks/figures/subgraph_weights.png.

Run from the project root:
    .venv/bin/python connectome/analyze_subgraph.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

EDGES = Path("connectome/data/subgraph_v783/edges.csv")
ANALYSIS = Path("connectome/data/subgraph_v783/analysis.json")
FIGURE = Path("notebooks/figures/subgraph_weights.png")
THRESHOLDS = (1, 2, 3, 5, 10)
GROUPS = ["post_side", "pre_type"]


def top_share(values: pd.Series, fraction: float = 0.10) -> float:
    """Share of the total held by the strongest `fraction` of items (at least one item)."""
    v = np.sort(values.to_numpy())[::-1]
    if v.sum() == 0:
        return 0.0
    k = max(1, math.ceil(fraction * len(v)))
    return float(v[:k].sum() / v.sum())


def weight_stats(edges: pd.DataFrame) -> pd.DataFrame:
    """Per (giant fiber side, source type): neuron count and spread of synapses per neuron."""
    rows = []
    for (side, cell_type), g in edges.groupby(GROUPS):
        s = g.syn_count
        rows.append(
            {
                "post_side": side,
                "pre_type": cell_type,
                "neurons": len(g),
                "synapses": int(s.sum()),
                "mean": round(float(s.mean()), 2),
                "median": float(s.median()),
                "min": int(s.min()),
                "max": int(s.max()),
                "top10pct_share": round(top_share(s), 3),
            }
        )
    return pd.DataFrame(rows)


def threshold_effect(edges: pd.DataFrame, thresholds=THRESHOLDS) -> pd.DataFrame:
    """What is left per giant fiber side if connections below `threshold` synapses are dropped."""
    rows = []
    for side, g in edges.groupby("post_side"):
        total_n, total_s = len(g), int(g.syn_count.sum())
        for thr in thresholds:
            kept = g[g.syn_count >= thr]
            rows.append(
                {
                    "post_side": side,
                    "min_synapses": thr,
                    "neurons_kept": len(kept),
                    "neurons_kept_pct": round(100 * len(kept) / total_n, 1),
                    "synapses_kept_pct": round(100 * kept.syn_count.sum() / total_s, 1),
                }
            )
    return pd.DataFrame(rows)


def make_figure(edges: pd.DataFrame, path: Path) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    colors = {"LPLC2": "#002060", "LC4": "#C00000"}
    bins = np.arange(0.5, edges.syn_count.max() + 1.5, 1)
    for cell_type, g in edges.groupby("pre_type"):
        ax1.hist(g.syn_count, bins=bins, alpha=0.6, color=colors[cell_type], label=cell_type)
    ax1.axvline(4.5, color="grey", ls="--")
    ax1.text(4.7, ax1.get_ylim()[1] * 0.9, "5 synapses", color="grey")
    ax1.set_xlabel("synapses in one connection")
    ax1.set_ylabel("number of connections")
    ax1.set_title("Connections range from 1 to 16 synapses")
    ax1.legend()
    for (side, cell_type), g in edges.groupby(GROUPS):
        v = np.sort(g.syn_count.to_numpy())[::-1]
        ax2.plot(
            np.arange(1, len(v) + 1) / len(v),
            np.cumsum(v) / v.sum(),
            color=colors[cell_type],
            ls="-" if side == "left" else ":",
            label=f"{cell_type} {side}",
        )
    ax2.plot([0, 1], [0, 1], color="lightgrey")
    ax2.set_xlabel("fraction of neurons (strongest first)")
    ax2.set_ylabel("fraction of synapses")
    ax2.set_title("How concentrated is the input?")
    ax2.legend()
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> None:
    edges = pd.read_csv(EDGES)
    stats = weight_stats(edges)
    sweep = threshold_effect(edges)
    print("== synapses per source neuron\n", stats.to_string(index=False))
    print("\n== if connections below N synapses are dropped\n", sweep.to_string(index=False))
    ANALYSIS.write_text(
        json.dumps(
            {
                "weight_stats": stats.to_dict("records"),
                "threshold_effect": sweep.to_dict("records"),
            },
            indent=2,
        )
        + "\n"
    )
    make_figure(edges, FIGURE)
    print(f"\nwrote {ANALYSIS} and {FIGURE}")


if __name__ == "__main__":
    main()
