"""Phase 3C: is the left/right asymmetry of the giant-fiber input specific to LPLC2 / LC4?

Question behind decisions_log 14: the right giant fiber gets 27% more synapses from our LPLC2 and LC4
neurons than the left one. Two checks:

1. Does the right giant fiber get more input from *every* kind of neuron (a property of the giant fiber
   or of how completely it was traced), or only from LPLC2 / LC4?
2. Do the left source neurons look less complete overall (fewer total input and output synapses)?
   That would point to a data-quality difference, not biology.

Reads connectome/data/raw/proofread_connections_783.feather and the annotation file.
Writes connectome/data/subgraph_v783/asymmetry.json.

Run from the project root:   .venv/bin/python -m connectome.asymmetry_check
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.feather as pf

from connectome.build_subgraph import SOURCE_TYPES, load_annotations, select_giant_fibers

RAW = Path("connectome/data/raw")
OUT = Path("connectome/data/subgraph_v783/asymmetry.json")


def load_relevant(path: Path, ids: list[int]) -> pd.DataFrame:
    """Connections where one end is a neuron of interest (summed over neuropils later)."""
    t = pf.read_table(path, columns=["pre_pt_root_id", "post_pt_root_id", "syn_count"])
    wanted = pa.array(ids, type=t.schema.field(0).type)
    mask = pc.or_(
        pc.is_in(t["pre_pt_root_id"], value_set=wanted),
        pc.is_in(t["post_pt_root_id"], value_set=wanted),
    )
    return t.filter(mask).to_pandas()


def gf_input_by_kind(conn: pd.DataFrame, ann: pd.DataFrame) -> pd.DataFrame:
    """Synapses into each giant fiber, split into LPLC2, LC4 and everything else."""
    gf = select_giant_fibers(ann).set_index("root_id")
    lookup = ann.set_index("root_id").cell_type
    inp = conn[conn.post_pt_root_id.isin(gf.index)].copy()
    inp["gf_side"] = inp.post_pt_root_id.map(gf.side)
    pre_type = inp.pre_pt_root_id.map(lookup)
    inp["kind"] = pre_type.where(pre_type.isin(SOURCE_TYPES), "other")
    table = inp.pivot_table(index="kind", columns="gf_side", values="syn_count", aggfunc="sum")
    table = table.fillna(0).astype(int)
    table["right_over_left"] = (table["right"] / table["left"]).round(2)
    return table


def source_completeness(conn: pd.DataFrame, ann: pd.DataFrame) -> pd.DataFrame:
    """Median total input and output synapses of the source neurons, by side and cell type."""
    src = ann[ann.cell_type.isin(SOURCE_TYPES)].set_index("root_id")
    syn_in = conn[conn.post_pt_root_id.isin(src.index)].groupby("post_pt_root_id").syn_count.sum()
    syn_out = conn[conn.pre_pt_root_id.isin(src.index)].groupby("pre_pt_root_id").syn_count.sum()
    df = src[["cell_type", "side"]].copy()
    df["input_synapses"] = syn_in.reindex(df.index).fillna(0)
    df["output_synapses"] = syn_out.reindex(df.index).fillna(0)
    return (
        df.groupby(["cell_type", "side"])[["input_synapses", "output_synapses"]]
        .median()
        .round(0)
        .astype(int)
    )


def main() -> None:
    ann = load_annotations(RAW / "Supplemental_file1_neuron_annotations.tsv")
    ids = (
        ann[ann.cell_type.isin(SOURCE_TYPES)].root_id.tolist()
        + select_giant_fibers(ann).root_id.tolist()
    )
    conn = load_relevant(RAW / "proofread_connections_783.feather", ids)
    by_kind = gf_input_by_kind(conn, ann)
    done = source_completeness(conn, ann)
    print("== synapses into each giant fiber, by kind of presynaptic neuron\n", by_kind.to_string())
    print(
        "\n== median total synapses of the source neurons (all their partners)\n", done.to_string()
    )
    OUT.write_text(
        json.dumps(
            {
                "gf_input_by_kind": by_kind.reset_index().to_dict("records"),
                "source_median_totals": done.reset_index().to_dict("records"),
            },
            indent=2,
        )
        + "\n"
    )
    print("\nwrote", OUT)


if __name__ == "__main__":
    main()
