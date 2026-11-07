"""Receptive-field centres for the LPLC2 and LC4 neurons (Phase 5.4).

Each neuron's receptive-field centre comes from where its input synapses sit in the lobula
(sampled synapse centroids, decisions_log 19), turned into a position on the 12 x 12 grid.

Method, per side (left eye -> left half of the camera image, right eye -> right half):
1. The lobula centroids form a thin sheet. Its normal is the direction of least spread.
2. "Up" on the sheet = the brain's dorsal direction projected onto the sheet. Checked from the
   data: FlyWire y grows ventrally (dorsal cell classes have small y, neck-end classes large y),
   and the dorsal-ventral axis is not inverted between eye and lobula.
3. "Back" on the sheet = the in-sheet direction perpendicular to up, oriented towards posterior
   (FlyWire z grows posteriorly). ASSUMPTION: the two optic chiasms invert the front-back axis
   twice, so the anterior lobula sees the frontal visual field. Not verified; the opposite
   mapping (flip_horizontal=True) is the pre-registered sensitivity check.
4. Each axis is scaled linearly so its 2nd to 98th percentile spans the half-image, clipped.
   Frontal maps to the image centre, posterior to the outer edge.
Declared simplification: a fly eye covers roughly 160 degrees; here each eye's whole map is
squeezed into a 30 x 60 degree half of the camera image.

Run from the project root:   .venv/bin/python -m fly.receptive_fields [--centroids PATH]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

GRID = 12
CELL_DEG = 5.0
OUT = Path("connectome/data/subgraph_v783/receptive_fields.csv")
FIG = Path("notebooks/figures/receptive_fields.png")
DEFAULT_CENTROIDS = Path("connectome/data/subgraph_v783/rf_sample15_centroids.csv")


def sheet_axes(xyz: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Unit vectors (up, back, normal) of the sheet, in brain coordinates (x, y, z)."""
    centred = xyz - xyz.mean(axis=0)
    normal = np.linalg.svd(centred, full_matrices=False)[2][2]
    dorsal = np.array([0.0, -1.0, 0.0])  # FlyWire y grows ventrally
    up = dorsal - dorsal.dot(normal) * normal
    up /= np.linalg.norm(up)
    back = np.cross(normal, up)
    if back[2] < 0:  # orient towards posterior (FlyWire z grows posteriorly)
        back = -back
    return up, back, normal


def scale01(v: np.ndarray, lo_pct: float = 2.0, hi_pct: float = 98.0) -> np.ndarray:
    lo, hi = np.percentile(v, [lo_pct, hi_pct])
    return np.clip((v - lo) / (hi - lo), 0.0, 1.0)


def map_side(xyz: np.ndarray, side: str, flip_horizontal: bool = False) -> np.ndarray:
    """Grid positions [N, 2] as (row, col) in cell units, 0..GRID, for one eye."""
    up, back, _ = sheet_axes(xyz)
    centred = xyz - xyz.mean(axis=0)
    height = scale01(centred @ up)  # 1 = most dorsal
    lateral = scale01(centred @ back)  # 1 = most posterior = outer edge of the image
    if flip_horizontal:
        lateral = 1.0 - lateral
    row = GRID * (1.0 - height)
    half = GRID / 2
    col = half * (1.0 - lateral) if side == "left" else half + half * lateral
    return np.stack([row, col], axis=1)


def build(centroids: pd.DataFrame, flip_horizontal: bool = False) -> pd.DataFrame:
    """One row per neuron: grid position and angle of its receptive-field centre."""
    lo = centroids[centroids.layer == "LO"].copy()
    parts = []
    for side, d in lo.groupby("side"):
        rc = map_side(d[["cx", "cy", "cz"]].to_numpy(), side, flip_horizontal)
        parts.append(d.assign(row=rc[:, 0], col=rc[:, 1]))
    out = pd.concat(parts)
    out["azimuth_deg"] = (out.col - GRID / 2) * CELL_DEG  # negative = left of centre
    out["elevation_deg"] = (GRID / 2 - out.row) * CELL_DEG  # positive = up
    cols = ["root_id", "cell_type", "side", "n_sites", "row", "col", "azimuth_deg"]
    return out[cols + ["elevation_deg"]].sort_values(["side", "cell_type", "root_id"])


def make_figure(rf: pd.DataFrame, path: Path = FIG) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 6.5))
    styles = {"LPLC2": ("o", "#1f77b4"), "LC4": ("^", "#d62728")}
    for ct, (marker, colour) in styles.items():
        d = rf[rf.cell_type == ct]
        ax.scatter(d.col, d.row, s=22, marker=marker, color=colour, alpha=0.75, label=ct)
    ax.axvline(GRID / 2, color="k", lw=1)
    ax.set_xlim(0, GRID)
    ax.set_ylim(GRID, 0)
    ax.set_xticks(range(GRID + 1))
    ax.set_yticks(range(GRID + 1))
    ax.grid(alpha=0.3)
    ax.set_aspect("equal")
    ax.set_xlabel("grid column (5 degrees each)   left eye | right eye")
    ax.set_ylabel("grid row (top = up)")
    ax.legend(loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.2))
    ax.set_title("Receptive-field centres of LPLC2 and LC4 on the 12 x 12 grid")
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    print("wrote", path)


def main() -> None:
    p = argparse.ArgumentParser(description="map lobula centroids to grid positions")
    p.add_argument("--centroids", type=Path, default=DEFAULT_CENTROIDS)
    a = p.parse_args()
    cen = pd.read_csv(a.centroids)
    rf = build(cen)
    nodes = pd.read_csv("connectome/data/subgraph_v783/nodes.csv")
    n_src = (nodes.role == "source").sum()
    print(f"mapped {len(rf)} of {n_src} source neurons from {a.centroids}")
    print(rf.groupby(["side", "cell_type"])[["row", "col"]].describe().round(1).to_string())
    rf.to_csv(OUT, index=False)
    print("wrote", OUT)
    make_figure(rf)


if __name__ == "__main__":
    main()
