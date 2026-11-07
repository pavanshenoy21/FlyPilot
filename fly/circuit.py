"""Phase 6.1: the assembled fly circuit.

    camera frames -> 12 x 12 grid -> Reichardt ON/OFF motion (fixed front end, fly/frontend.py)
      -> drive for each LPLC2 / LC4 neuron from motion inside its receptive field
      -> LIF network wired from FlyWire synapse counts (fly/lif.py): sources -> left / right giant fiber
    trigger = the first giant-fiber spike; threat side = the giant fiber that fired first;
    the drone dodges to the other side (locked decisions 5 and 21).

Fixed choices (none fitted to looming data; decisions_log 24):
- Receptive field: every grid cell whose centre lies within RF_RADIUS_CELLS of the neuron's
  receptive-field centre (fly/receptive_fields.py). 2 cells = 10 degrees on our grid; the
  diameter (about 4 cells) is about a third of the grid height, roughly the share of the fly eye an
  LPLC2 receptive field covers (published LPLC2 receptive fields are about 60 degrees; value from
  memory, citation to check: Klapoetke et al. 2017).
- LPLC2 drive: mean over its receptive field of (outward - inward) motion relative to its centre,
  both polarities, rectified. LPLC2 prefers motion away from its centre in all directions and is
  inhibited by inward motion (Klapoetke et al. 2017).
- LC4 drive: mean outward motion only (no inward inhibition). Feeding LC4 the same motion signal is
  the declared simplification of locked decision 11.
- Weights: transmitter sign x synapse count x 0.275 mV, the published value of Shiu et al. 2024
  (configs/lif_params.yaml). Fixed.
- Input gain = THE ONE TUNED NUMBER (decisions_log 25, amending locked decision 3; Pavan approved).
  It is expressed relative to a reference: input_gain = 1 means a reference edge (the 5.3 moving
  bar, 60 deg/s, 10 deg wide) crossing one cell, if it filled the receptive field, would bring a
  neuron exactly to threshold. Phase 6.3 tunes input_gain once on the calibration set.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from fly.frontend import GRID, coarse_grid, reichardt
from fly.lif import LIFNetwork, LIFParams, SpikeRecord, load_params, synaptic_matrix

DATA = Path("connectome/data/subgraph_v783")
RF_RADIUS_CELLS = 2.0
FRAME_MS = 1000.0 / 30.0


@dataclass
class Circuit:
    node_ids: list[int]
    cell_type: np.ndarray  # per node
    side: np.ndarray  # per node
    source_idx: np.ndarray  # node indices of LPLC2 / LC4 neurons
    gf_idx: dict  # {"left": node index, "right": node index}
    kernels: np.ndarray  # [n_sources, 4 directions, GRID, GRID] drive weights
    counts: np.ndarray  # signed synapse-count matrix [post, pre], before scaling
    unit_gain_mV: float  # mV of input per unit of drive at input_gain = 1
    params: LIFParams


def reference_energy() -> float:
    """Peak one-direction motion energy of a single cell when the 5.3 reference bar crosses it."""
    from sim.stimuli import moving_bar

    m = reichardt(coarse_grid(moving_bar("right"))).sum(axis=1)  # [T, 4, n, n]
    return float(m[:, 0].max())


def kernels_for(rows: np.ndarray, cols: np.ndarray, types: np.ndarray, radius: float) -> np.ndarray:
    """Per neuron, weights on the 4 direction maps: outward +1, inward -1 (LPLC2) or 0 (LC4),
    averaged over the cells of the receptive field."""
    cy, cx = np.mgrid[0:GRID, 0:GRID] + 0.5
    k = np.zeros((len(rows), 4, GRID, GRID))
    for i, (r, c, t) in enumerate(zip(rows, cols, types, strict=True)):
        dx, dy = cx - c, cy - r
        inside = np.hypot(dx, dy) <= radius
        if not inside.any():  # always use at least the nearest cell
            inside = np.hypot(dx, dy) == np.hypot(dx, dy).min()
        inhibit = 1.0 if t == "LPLC2" else 0.0
        right, left = np.sign(dx) > 0, np.sign(dx) < 0
        down, up = np.sign(dy) > 0, np.sign(dy) < 0
        k[i, 0] = right * 1.0 - left * inhibit  # rightward motion: outward on the right side
        k[i, 1] = left * 1.0 - right * inhibit
        k[i, 2] = down * 1.0 - up * inhibit
        k[i, 3] = up * 1.0 - down * inhibit
        k[i] *= inside / inside.sum()
    return k


def load_circuit(
    data: Path = DATA, radius: float = RF_RADIUS_CELLS, flip_horizontal: bool = False
) -> Circuit:
    nodes = pd.read_csv(data / "nodes.csv")
    edges = pd.read_csv(data / "edges.csv")
    rf = pd.read_csv(data / "receptive_fields.csv").set_index("root_id")
    ids = nodes.root_id.tolist()
    src = nodes[nodes.role == "source"]
    src_rf = rf.loc[src.root_id]
    cols = src_rf.col.to_numpy()
    if flip_horizontal:  # the pre-registered sensitivity check (decisions_log 22)
        half = GRID / 2
        left = src.side.to_numpy() == "left"  # flip within each eye, by the neuron's real side
        cols = np.where(left, half - cols, 3 * half - cols)
    gf = nodes[nodes.role == "giant_fiber"]
    params = load_params()
    return Circuit(
        node_ids=ids,
        cell_type=nodes.cell_type.to_numpy(),
        side=nodes.side.to_numpy(),
        source_idx=np.array([ids.index(r) for r in src.root_id]),
        gf_idx={s: ids.index(r) for s, r in zip(gf.side, gf.root_id, strict=True)},
        kernels=kernels_for(src_rf.row.to_numpy(), cols, src.cell_type.to_numpy(), radius),
        counts=synaptic_matrix(
            ids,
            edges.pre_root_id.tolist(),
            edges.post_root_id.tolist(),
            edges.syn_count.tolist(),
            edges.nt_neuron.tolist(),
            scale_mV=1.0,
        ),
        unit_gain_mV=(params.v_thresh_mV - params.v_rest_mV) / reference_energy(),
        params=params,
    )


def source_drive(circuit: Circuit, frames: np.ndarray, input_gain: float = 1.0) -> np.ndarray:
    """Input in mV for every source neuron at every frame: [T, n_sources]."""
    motion = reichardt(coarse_grid(frames)).sum(axis=1)  # both polarities: [T, 4, n, n]
    drive = np.einsum("tdij,sdij->ts", motion, circuit.kernels)
    return np.maximum(drive, 0.0) * circuit.unit_gain_mV * input_gain


@dataclass
class Response:
    record: SpikeRecord
    trigger_ms: float | None  # first giant-fiber spike
    threat_side: str | None  # side of the giant fiber that fired first
    gf_spikes: dict  # {"left": count, "right": count}
    source_spikes: int


def run(circuit: Circuit, frames: np.ndarray, input_gain: float) -> Response:
    """Run one stimulus. Frames are held for one frame period each (zero-order hold)."""
    p = circuit.params
    net = LIFNetwork(circuit.counts * p.w_syn_mV, p)
    drive = source_drive(circuit, frames, input_gain)
    steps_per_frame = round(FRAME_MS / p.dt_ms)
    record = SpikeRecord.empty(net.n, p.dt_ms)
    i_ext = np.zeros(net.n)
    for f in range(len(frames)):
        i_ext[circuit.source_idx] = drive[f]
        for k in range(steps_per_frame):
            record.add(f * steps_per_frame + k, net.step(i_ext))
    first = {s: record.first_spike_ms(i) for s, i in circuit.gf_idx.items()}
    fired = {s: t for s, t in first.items() if t is not None}
    trigger = min(fired.values()) if fired else None
    side = min(fired, key=fired.get) if fired else None
    counts = record.counts()
    return Response(
        record=record,
        trigger_ms=trigger,
        threat_side=side,
        gf_spikes={s: int(counts[i]) for s, i in circuit.gf_idx.items()},
        source_spikes=int(counts[circuit.source_idx].sum()),
    )


def make_figure(
    input_gain: float, seed: int = 1, path: str = "notebooks/figures/circuit_raster.png"
):
    """Spike raster for one looming stimulus: every LPLC2 / LC4 spike, and the giant fibers."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from sim.stimuli import make_stimulus

    c = load_circuit()
    s = make_stimulus("looming", seed)
    r = run(c, s.frames, input_gain)
    impact_ms = s.ttc_s[0] * 1000
    order = sorted(c.source_idx, key=lambda i: (c.side[i], c.cell_type[i]))
    row_of = {node: k for k, node in enumerate(order)}
    gf_rows = {c.gf_idx["left"]: len(order) + 8, c.gf_idx["right"]: len(order) + 20}
    t = r.record.times_ms
    neurons = np.asarray(r.record.neurons)
    fig, ax = plt.subplots(figsize=(10, 6))
    colours = {"LPLC2": "#1f77b4", "LC4": "#d62728"}
    for ct, col in colours.items():
        m = np.array([c.cell_type[n] == ct and n in row_of for n in neurons], dtype=bool)
        ax.scatter(t[m] - impact_ms, [row_of[n] for n in neurons[m]], s=2, color=col, label=ct)
    gm = np.isin(neurons, list(gf_rows))
    ax.scatter(
        t[gm] - impact_ms,
        [gf_rows[n] for n in neurons[gm]],
        s=40,
        marker="|",
        color="k",
        label="giant fibers",
    )
    if r.trigger_ms is not None:
        ax.axvline(r.trigger_ms - impact_ms, color="k", ls="--", lw=1)
        ax.text(
            r.trigger_ms - impact_ms - 10,
            len(order) * 0.75,
            f"trigger: {r.threat_side} giant fiber\n{impact_ms - r.trigger_ms:.0f} ms before impact",
            ha="right",
        )
    ax.set_xlim(-800, 0)
    ax.set_ylim(-2, len(order) + 28)
    half = sum(c.side[i] == "left" for i in order)
    ax.axhline(half - 0.5, color="grey", lw=0.5)
    ax.set_yticks([half / 2, half + (len(order) - half) / 2, len(order) + 8, len(order) + 20])
    ax.set_yticklabels(["left eye\nLPLC2 + LC4", "right eye\nLPLC2 + LC4", "left GF", "right GF"])
    ax.set_xlabel("time to impact (ms)")
    ax.legend(loc="center left", markerscale=4)
    ax.set_title(
        f"One looming stimulus through the fly circuit (input gain {input_gain}, "
        "placeholder before calibration)"
    )
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    print("wrote", path)
    return r
