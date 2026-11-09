"""Phase 7.1: degree-preserving rewire of the fly circuit (locked decision 12).

Configuration-model style: the list of edge targets is randomly permuted across edges, so
- every neuron keeps its out-degree and its in-degree,
- every edge keeps its synapse count and its presynaptic neuron's transmitter (so each neuron's
  total output synapses, the total synapse count and the sign counts are unchanged),
- only WHO CONNECTS TO WHOM changes.
A draw that would create a duplicate edge or a self-connection is rejected and redrawn.

Structure of our circuit (checked on the data): 293 sources, each with exactly one edge, to the
giant fiber on its own side (148 left, 145 right). So here a degree-preserving rewire amounts to a
random choice of which giant fiber each source drives, with 148 going left and 145 right. On
average about half of each eye then drives the opposite giant fiber. The test therefore mainly
asks whether the real left/right routing matters; the receptive-field map and the front end are
shared with the real circuit (locked decision 8).

Run: .venv/bin/python -m fly.shuffle   (writes logs/shuffle_wiring_summary.csv for seeds 0-19)
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import numpy as np
import pandas as pd

from fly.circuit import DATA, Circuit, load_circuit
from fly.lif import synaptic_matrix, transmitter_sign

SUMMARY = Path("logs/shuffle_wiring_summary.csv")


def rewire(edges: pd.DataFrame, seed: int, max_tries: int = 10_000) -> pd.DataFrame:
    """Return a copy of edges with post_root_id permuted across edges (configuration model)."""
    rng = np.random.default_rng(seed)
    pre = edges.pre_root_id.to_numpy()
    for _ in range(max_tries):
        post = rng.permutation(edges.post_root_id.to_numpy())
        no_self = not np.any(pre == post)
        no_dupes = not pd.DataFrame({"a": pre, "b": post}).duplicated().any()
        if no_self and no_dupes:
            break
    else:
        raise RuntimeError(f"no valid rewire in {max_tries} tries (seed {seed})")
    out = edges.copy()
    out["post_root_id"] = post
    if "post_side" in out and "pre_side" in out:  # keep the descriptive columns consistent
        side = dict(zip(edges.post_root_id, edges.post_side, strict=False))
        out["post_side"] = out.post_root_id.map(side)
        out["same_side"] = out.pre_side == out.post_side
    return out


def preserved(real: pd.DataFrame, shuf: pd.DataFrame) -> dict:
    """Every property the shuffle must keep (Gate G3). All values must be True."""

    def deg(df, col):
        return df.groupby(col).size().sort_index()

    def strength(df, col):
        return df.groupby(col).syn_count.sum().sort_index()

    def signs(df):
        return df.nt_neuron.map(transmitter_sign).value_counts().sort_index()

    return {
        "out_degree": deg(real, "pre_root_id").equals(deg(shuf, "pre_root_id")),
        "in_degree": deg(real, "post_root_id").equals(deg(shuf, "post_root_id")),
        "out_synapses": strength(real, "pre_root_id").equals(strength(shuf, "pre_root_id")),
        "total_synapses": int(real.syn_count.sum()) == int(shuf.syn_count.sum()),
        "synapse_counts": sorted(real.syn_count) == sorted(shuf.syn_count),
        "sign_counts": signs(real).equals(signs(shuf)),
        "transmitter_per_neuron": real.groupby("pre_root_id")
        .nt_neuron.first()
        .equals(shuf.groupby("pre_root_id").nt_neuron.first()),
        "no_duplicates": not shuf[["pre_root_id", "post_root_id"]].duplicated().any(),
        "no_self_edges": not (shuf.pre_root_id == shuf.post_root_id).any(),
        "n_edges": len(real) == len(shuf),
    }


def shuffled_circuit(seed: int, base: Circuit | None = None, data: Path = DATA) -> Circuit:
    """The real circuit with only its wiring replaced (same neurons, receptive fields, gains)."""
    base = base if base is not None else load_circuit(data)
    edges = rewire(pd.read_csv(data / "edges.csv"), seed)
    counts = synaptic_matrix(
        base.node_ids,
        edges.pre_root_id.tolist(),
        edges.post_root_id.tolist(),
        edges.syn_count.tolist(),
        edges.nt_neuron.tolist(),
        scale_mV=1.0,
    )
    return dataclasses.replace(base, counts=counts)


def describe(edges: pd.DataFrame) -> dict:
    """How the wiring routes each eye: share of edges (and synapses) that stay on their own side."""
    same = edges.pre_side == edges.post_side
    into = edges.groupby("post_side")
    return {
        "same_side_edges": float(same.mean()),
        "same_side_synapses": float(edges.syn_count[same].sum() / edges.syn_count.sum()),
        "gf_left_in_degree": int(into.size().get("left", 0)),
        "gf_right_in_degree": int(into.size().get("right", 0)),
        "gf_left_synapses": int(into.syn_count.sum().get("left", 0)),
        "gf_right_synapses": int(into.syn_count.sum().get("right", 0)),
    }


def main(seeds=range(20), data: Path = DATA) -> pd.DataFrame:
    real = pd.read_csv(data / "edges.csv")
    rows = [{"wiring": "real", "seed": None, **describe(real), "all_preserved": True}]
    for s in seeds:
        shuf = rewire(real, s)
        checks = preserved(real, shuf)
        rows.append(
            {
                "wiring": "shuffled",
                "seed": s,
                **describe(shuf),
                "all_preserved": all(checks.values()),
            }
        )
    df = pd.DataFrame(rows)
    SUMMARY.parent.mkdir(exist_ok=True)
    df.to_csv(SUMMARY, index=False)
    with pd.option_context("display.width", 160):
        print(df.to_string(index=False))
    print("wrote", SUMMARY)
    return df


if __name__ == "__main__":
    main()
