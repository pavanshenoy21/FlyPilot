"""Phase 3B: can each neuron's receptive-field position be recovered from synapse locations?

Idea: the dendrites of LPLC2 and LC4 neurons sit in the lobula (LO) and lobula plate (LOP), which are
retinotopic layers, so the centre of a neuron's input synapses there says where in the visual field it looks.

The FlyWire synapse table (9.5 GB, Zenodo) is shuffled, so we cannot fetch one neuron's rows. Every batch is a
random sample of all synapses, so a random subset of batches is an unbiased sample for every neuron. This
script reads only the chosen batches with HTTP range requests, keeps the rows whose postsynaptic neuron is one
of our source neurons and whose neuropil is LO or LOP, and computes per-neuron centroids.

Outputs:
    connectome/data/raw/rf_probe_synapses.feather        (the filtered rows, not tracked in Git)
    connectome/data/subgraph_v783/rf_probe_centroids.csv (per-neuron centroids and a split-half check)
    notebooks/figures/receptive_field_probe.png

Run from the project root:   .venv/bin/python connectome/probe_receptive_fields.py [--batches 40] [--seed 0]

Units (checked 7 Nov 2026): positions in the synapse table are in nanometres on all three axes. Compared with the
annotation file, whose positions are in 4 x 4 x 40 nm voxels, the table values are about 4x larger in x (the
left/right distance) and about 40-60x larger in z, which is what nanometres against those voxels would give.
"""

from __future__ import annotations

import argparse
import io
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import pyarrow as pa
from pyarrow import ipc

matplotlib.use("Agg")
import matplotlib.pyplot as plt

URL = "https://zenodo.org/api/records/10676866/files/flywire_synapses_783.feather/content"
NODES = Path("connectome/data/subgraph_v783/nodes.csv")
RAW_OUT = Path("connectome/data/raw/rf_probe_synapses.feather")
CSV_OUT = Path("connectome/data/subgraph_v783/rf_probe_centroids.csv")
FIG_OUT = Path("notebooks/figures/receptive_field_probe.png")
UM_PER_UNIT = (
    0.001  # the synapse table stores positions in nanometres (see the note in the docstring)
)
NEUROPILS = ("LO_L", "LO_R", "LOP_L", "LOP_R")
COLUMNS = [
    "post_pt_root_id",
    "neuropil",
    "post_pt_position_x",
    "post_pt_position_y",
    "post_pt_position_z",
]
HEADERS = {"User-Agent": "curl-client"}


class HttpFile(io.RawIOBase):
    """A read-only file backed by HTTP range requests (so Arrow can read a few batches only)."""

    def __init__(self, url: str):
        req = urllib.request.Request(url, method="HEAD", headers=HEADERS)
        with urllib.request.urlopen(req, timeout=60) as resp:
            self.size = int(resp.headers["Content-Length"])
        self.url, self.pos, self.bytes_read = url, 0, 0

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        base = {0: 0, 1: self.pos, 2: self.size}[whence]
        self.pos = base + offset
        return self.pos

    def read(self, n=-1):
        n = self.size - self.pos if n is None or n < 0 else min(n, self.size - self.pos)
        if n <= 0:
            return b""
        headers = {**HEADERS, "Range": f"bytes={self.pos}-{self.pos + n - 1}"}
        for attempt in range(4):
            try:
                with urllib.request.urlopen(
                    urllib.request.Request(self.url, headers=headers), timeout=120
                ) as resp:
                    data = resp.read()
                break
            except OSError:
                if attempt == 3:
                    raise
                time.sleep(3 * (attempt + 1))
        self.pos += len(data)
        self.bytes_read += len(data)
        return data

    def readinto(self, b):
        data = self.read(len(b))
        b[: len(data)] = data
        return len(data)


def fetch_rows(url: str, batch_ids: list[int], neuron_ids: set[int]) -> tuple[pd.DataFrame, int]:
    """Read the given batches and keep lobula rows of the wanted postsynaptic neurons."""
    f = HttpFile(url)
    reader = ipc.open_file(pa.PythonFile(f, mode="r"))
    keep = []
    for i in batch_ids:
        df = reader.get_batch(i).select(COLUMNS).to_pandas()
        df = df[df.post_pt_root_id.isin(neuron_ids) & df.neuropil.isin(NEUROPILS)]
        keep.append(df.assign(batch=i))
    return pd.concat(keep, ignore_index=True), f.bytes_read


def centroids(rows: pd.DataFrame, min_sites: int = 1) -> pd.DataFrame:
    """Per neuron and per layer (LO / LOP): number of sites, centroid (um) and spread (um)."""
    out = []
    pos = rows[[f"post_pt_position_{a}" for a in "xyz"]].to_numpy(float) * UM_PER_UNIT
    rows = rows.assign(x=pos[:, 0], y=pos[:, 1], z=pos[:, 2])
    rows["layer"] = rows.neuropil.str.split("_").str[0]
    for (nid, layer), g in rows.groupby(["post_pt_root_id", "layer"]):
        if len(g) < min_sites:
            continue
        xyz = g[["x", "y", "z"]].to_numpy()
        out.append(
            {
                "root_id": nid,
                "layer": layer,
                "n_sites": len(g),
                "cx": xyz[:, 0].mean(),
                "cy": xyz[:, 1].mean(),
                "cz": xyz[:, 2].mean(),
                "spread_um": float(np.sqrt(xyz.var(axis=0).sum())),
            }
        )
    return pd.DataFrame(out)


def split_half(rows: pd.DataFrame, min_sites: int = 5) -> pd.DataFrame:
    """Centroids from two disjoint sets of batches; the distance between them is the sampling error."""
    batches = np.sort(rows.batch.unique())
    a = centroids(rows[rows.batch.isin(batches[::2])], min_sites).set_index(["root_id", "layer"])
    b = centroids(rows[rows.batch.isin(batches[1::2])], min_sites).set_index(["root_id", "layer"])
    both = a.join(b, lsuffix="_a", rsuffix="_b", how="inner")
    both["half_distance_um"] = np.sqrt(
        (both.cx_a - both.cx_b) ** 2 + (both.cy_a - both.cy_b) ** 2 + (both.cz_a - both.cz_b) ** 2
    )
    return both.reset_index()[["root_id", "layer", "half_distance_um"]]


def run(n_batches: int, seed: int, workers: int = 4, reuse: bool = False) -> None:
    nodes = pd.read_csv(NODES)
    src = nodes[nodes.role == "source"]
    ids = set(src.root_id.astype("int64"))
    if reuse:
        rows = pd.read_feather(RAW_OUT)
        print(f"reusing the saved sample: {len(rows):,} rows from {rows.batch.nunique()} batches")
    else:
        total = ipc.open_file(pa.PythonFile(HttpFile(URL), mode="r")).num_record_batches
        chosen = np.random.default_rng(seed).choice(total, size=n_batches, replace=False).tolist()
        chunks = [chosen[i::workers] for i in range(workers)]
        t0 = time.time()
        with ThreadPoolExecutor(workers) as pool:
            results = list(pool.map(lambda c: fetch_rows(URL, c, ids), chunks))
        rows = pd.concat([r for r, _ in results], ignore_index=True)
        mb = sum(b for _, b in results) / 1e6
        print(
            f"read {n_batches} of {total} batches ({mb:.0f} MB) in {time.time() - t0:.0f}s; kept {len(rows):,} rows"
        )
        RAW_OUT.parent.mkdir(parents=True, exist_ok=True)
        rows.to_feather(RAW_OUT)

    cen = centroids(rows).merge(
        src[["root_id", "cell_type", "side"]].astype({"root_id": "int64"}), on="root_id"
    )
    sh = split_half(rows)
    cen = cen.merge(sh, on=["root_id", "layer"], how="left")
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    cen.to_csv(CSV_OUT, index=False)

    lo = cen[cen.layer == "LO"]
    print(f"\nneurons with at least one LO site: {len(lo)} of {len(src)}")
    print(
        "LO sites per neuron (sampled): median",
        int(lo.n_sites.median()),
        "| 5th percentile",
        int(lo.n_sites.quantile(0.05)),
    )
    ok = lo.dropna(subset=["half_distance_um"])
    print(f"split-half check on {len(ok)} neurons with >=5 sites in each half:")
    print(
        f"  median distance between the two centroid estimates: {ok.half_distance_um.median():.1f} um"
    )
    for (side, ct), g in lo.groupby(["side", "cell_type"]):
        print(
            f"  LO centroids {side:5} {ct:6}: spread across neurons (std of x,y,z) = "
            f"{g.cx.std():.1f}, {g.cy.std():.1f}, {g.cz.std():.1f} um  (n={len(g)})"
        )
    make_figure(lo)


def make_figure(lo: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2))
    colors = {"LPLC2": "#002060", "LC4": "#C00000"}
    for ax, side in zip(axes, ["left", "right"], strict=True):
        g = lo[lo.side == side]
        for ct, gg in g.groupby("cell_type"):
            ax.scatter(gg.cx, gg.cy, s=28, color=colors[ct], alpha=0.8, label=f"{ct} (n={len(gg)})")
        ax.set_title(f"{side} lobula: centre of each neuron's input synapses", fontsize=13)
        ax.set_xlabel("x (um)")
        ax.set_ylabel("y (um)")
        ax.set_aspect("equal", adjustable="datalim")
        ax.legend()
    fig.tight_layout()
    FIG_OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_OUT, dpi=150)
    plt.close(fig)
    print("wrote", FIG_OUT)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--batches", type=int, default=40)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument(
        "--reuse", action="store_true", help="reuse the saved sample instead of fetching"
    )
    p.add_argument(
        "--tag",
        default="",
        help="name the outputs rf_<tag>_* instead of rf_probe_* (keeps the pinned G1 probe intact)",
    )
    a = p.parse_args()
    if a.tag:
        global RAW_OUT, CSV_OUT, FIG_OUT
        RAW_OUT = RAW_OUT.with_name(f"rf_{a.tag}_synapses.feather")
        CSV_OUT = CSV_OUT.with_name(f"rf_{a.tag}_centroids.csv")
        FIG_OUT = FIG_OUT.with_name(f"receptive_field_{a.tag}.png")
    run(a.batches, a.seed, reuse=a.reuse)


if __name__ == "__main__":
    main()
