"""Build the LPLC2 / LC4 -> giant fiber subgraph from FlyWire snapshot 783 (Phase 2C).

Design (locked): direct connections only, from LPLC2 and LC4 neurons to the two giant fibers.
The giant fiber is cell type DNp01 (hemibrain label "Giant Fiber"), one per side.

Inputs (downloaded in Phase 2B, see configs/data_version.yaml):
    connectome/data/raw/proofread_connections_783.feather
    connectome/data/raw/Supplemental_file1_neuron_annotations.tsv

Outputs (small, tracked in Git):
    connectome/data/subgraph_v783/nodes.csv
    connectome/data/subgraph_v783/edges.csv
    connectome/data/subgraph_v783/summary.json

Run from the project root:
    .venv/bin/python connectome/build_subgraph.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import pyarrow.compute as pc
import pyarrow.feather as pf

SOURCE_TYPES = ("LPLC2", "LC4")
GIANT_FIBER_LABEL = "Giant Fiber"  # value of the `hemibrain_type` annotation

# connection-table probability columns -> transmitter names used in the annotation file
NT_COLUMNS = {
    "ach_avg": "acetylcholine",
    "gaba_avg": "gaba",
    "glut_avg": "glutamate",
    "oct_avg": "octopamine",
    "ser_avg": "serotonin",
    "da_avg": "dopamine",
}

# locked rule (decision 3, 6): ACh excitatory; GABA and glutamate inhibitory; others dropped
NT_SIGN = {"acetylcholine": 1, "gaba": -1, "glutamate": -1}

ANNOTATION_COLUMNS = [
    "root_id",
    "cell_type",
    "hemibrain_type",
    "side",
    "top_nt",
    "top_nt_conf",
    "known_nt",
    "known_nt_source",
    "pos_x",
    "pos_y",
    "pos_z",
    "soma_x",
    "soma_y",
    "soma_z",
]


def nt_sign(top_nt: object) -> int:
    """Return +1 / -1 for the locked transmitter rule, 0 for anything else (dropped)."""
    if not isinstance(top_nt, str):
        return 0
    return NT_SIGN.get(top_nt.strip().lower(), 0)


def load_annotations(path: Path) -> pd.DataFrame:
    ann = pd.read_csv(
        path,
        sep="\t",
        usecols=ANNOTATION_COLUMNS,
        dtype={"root_id": "int64"},
        low_memory=False,
    )
    if ann.root_id.duplicated().any():
        raise ValueError("annotation file has duplicate root_id values")
    return ann


def select_giant_fibers(ann: pd.DataFrame) -> pd.DataFrame:
    gf = ann[ann.hemibrain_type.fillna("") == GIANT_FIBER_LABEL]
    sides = sorted(gf.side.tolist())
    if sides != ["left", "right"]:
        raise ValueError(f"expected one left and one right giant fiber, found sides {sides}")
    return gf


def select_sources(ann: pd.DataFrame) -> pd.DataFrame:
    return ann[ann.cell_type.isin(SOURCE_TYPES)]


def read_connections_into(path: Path, post_ids: list[int]) -> pd.DataFrame:
    """Read only the rows whose postsynaptic neuron is one of `post_ids` (keeps memory small)."""
    table = pf.read_table(path)
    mask = pc.is_in(
        table["post_pt_root_id"], value_set=pc.cast(post_ids, table.schema.field(1).type)
    )
    return table.filter(mask).to_pandas()


def aggregate_edges(conn: pd.DataFrame, source_ids: set[int]) -> pd.DataFrame:
    """Collapse the per-neuropil rows into one row per (pre, post) neuron pair.

    Synapse counts are summed. Transmitter probabilities are averaged, weighted by synapse count.
    """
    conn = conn[conn.pre_pt_root_id.isin(source_ids)].copy()
    if conn.empty:
        return pd.DataFrame(
            columns=["pre_root_id", "post_root_id", "syn_count", "n_neuropils", *NT_COLUMNS]
        )
    for col in NT_COLUMNS:
        conn[col] = conn[col] * conn.syn_count
    grouped = conn.groupby(["pre_pt_root_id", "post_pt_root_id"], as_index=False).agg(
        syn_count=("syn_count", "sum"),
        n_neuropils=("neuropil", "nunique"),
        **{col: (col, "sum") for col in NT_COLUMNS},
    )
    for col in NT_COLUMNS:
        grouped[col] = grouped[col] / grouped.syn_count
    return grouped.rename(
        columns={"pre_pt_root_id": "pre_root_id", "post_pt_root_id": "post_root_id"}
    )


def build_subgraph(
    ann: pd.DataFrame, conn: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Return (nodes, edges, summary). `conn` must already be restricted to giant-fiber targets."""
    gf = select_giant_fibers(ann)
    sources = select_sources(ann)
    lookup = ann.set_index("root_id")

    edges = aggregate_edges(conn, set(sources.root_id))
    edges = edges[edges.post_root_id.isin(set(gf.root_id))].reset_index(drop=True)

    edges["pre_type"] = edges.pre_root_id.map(lookup.cell_type)
    edges["pre_side"] = edges.pre_root_id.map(lookup.side)
    edges["post_side"] = edges.post_root_id.map(lookup.side)
    edges["same_side"] = edges.pre_side == edges.post_side
    # Sign source (decision 13): the experimentally known transmitter when the annotation file
    # has one (e.g. Davis et al. 2020 for LPLC2 / LC4), otherwise FlyWire's prediction. The
    # per-connection probabilities in the connection table are kept for comparison only.
    known = edges.pre_root_id.map(lookup.known_nt)
    edges["nt_neuron"] = known.fillna(edges.pre_root_id.map(lookup.top_nt))
    edges["nt_source"] = known.notna().map({True: "known", False: "predicted"})
    edges["sign"] = edges.nt_neuron.map(nt_sign)
    probs = edges[list(NT_COLUMNS)]
    edges["nt_connection"] = (
        probs.idxmax(axis=1).map(NT_COLUMNS) if len(edges) else pd.Series(dtype=str)
    )
    edges["nt_agree"] = edges.nt_neuron.str.lower() == edges.nt_connection
    edges = edges.sort_values(["post_side", "pre_type", "pre_root_id"]).reset_index(drop=True)

    connected = set(edges.pre_root_id)
    node_rows = pd.concat(
        [
            gf.assign(role="giant_fiber"),
            sources[sources.root_id.isin(connected)].assign(role="source"),
        ]
    )
    nodes = node_rows[
        [
            "root_id",
            "role",
            "cell_type",
            "side",
            "top_nt",
            "top_nt_conf",
            "known_nt",
            "known_nt_source",
        ]
    ].copy()
    nodes = nodes.merge(
        node_rows[["root_id", "pos_x", "pos_y", "pos_z", "soma_x", "soma_y", "soma_z"]],
        on="root_id",
    )
    nodes = nodes.sort_values(["role", "side", "cell_type", "root_id"]).reset_index(drop=True)

    summary = summarise(sources, connected, edges)
    return nodes, edges, summary


def summarise(sources: pd.DataFrame, connected: set[int], edges: pd.DataFrame) -> dict:
    per_type: dict[str, dict] = {}
    for (cell_type, side), grp in sources.groupby(["cell_type", "side"]):
        total = len(grp)
        linked = int(grp.root_id.isin(connected).sum())
        per_type[f"{cell_type}_{side}"] = {
            "neurons_in_dataset": total,
            "neurons_with_direct_edge_to_gf": linked,
            "neurons_without_edge": total - linked,
        }
    per_gf: dict[str, dict] = {}
    for side, grp in edges.groupby("post_side"):
        per_gf[f"gf_{side}"] = {
            "presynaptic_neurons": len(grp),
            "synapses": int(grp.syn_count.sum()),
            "by_type": {
                t: {"neurons": len(g), "synapses": int(g.syn_count.sum())}
                for t, g in grp.groupby("pre_type")
            },
        }
    total_syn = int(edges.syn_count.sum())
    dropped = int(edges.loc[edges.sign == 0, "syn_count"].sum())
    return {
        "edges": len(edges),
        "synapses": total_syn,
        "same_side_fraction_by_synapse": float(
            edges.loc[edges.same_side, "syn_count"].sum() / total_syn
        )
        if total_syn
        else None,
        "sign_counts_by_edge": {str(k): int(v) for k, v in edges.sign.value_counts().items()},
        "synapses_dropped_unknown_transmitter": dropped,
        "edges_by_sign_source": {str(k): int(v) for k, v in edges.nt_source.value_counts().items()},
        "edges_where_neuron_and_connection_transmitter_disagree": int((~edges.nt_agree).sum()),
        "sources": per_type,
        "giant_fibers": per_gf,
    }


def write_outputs(nodes: pd.DataFrame, edges: pd.DataFrame, summary: dict, outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    nodes.to_csv(outdir / "nodes.csv", index=False)
    edges.to_csv(outdir / "edges.csv", index=False)
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--raw", type=Path, default=Path("connectome/data/raw"))
    parser.add_argument("--out", type=Path, default=Path("connectome/data/subgraph_v783"))
    args = parser.parse_args()

    ann = load_annotations(args.raw / "Supplemental_file1_neuron_annotations.tsv")
    gf = select_giant_fibers(ann)
    conn = read_connections_into(
        args.raw / "proofread_connections_783.feather", gf.root_id.tolist()
    )
    nodes, edges, summary = build_subgraph(ann, conn)
    write_outputs(nodes, edges, summary, args.out)
    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"\nwrote {len(nodes)} nodes and {len(edges)} edges to {args.out}")


if __name__ == "__main__":
    main()
