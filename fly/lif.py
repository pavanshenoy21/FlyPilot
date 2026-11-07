"""Generic leaky integrate-and-fire network (Phase 4). Knows nothing about flies.

Equations (Shiu et al. 2024, constants in configs/lif_params.yaml):
    dv/dt = (v_rest - v + g + i_ext) / tau_mem      frozen while refractory
    dg/dt = -g / tau_syn                            frozen while refractory
A neuron that crosses threshold resets (v = v_reset, g = 0), stays refractory for t_refrac, and
after t_delay adds W[target, source] to the g of every target. W is signed and in mV.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import yaml

TRANSMITTER_SIGN = {"acetylcholine": 1, "gaba": -1, "glutamate": -1}  # locked decision 3


@dataclass(frozen=True)
class LIFParams:
    dt_ms: float
    v_rest_mV: float
    v_reset_mV: float
    v_thresh_mV: float
    tau_mem_ms: float
    t_refrac_ms: float
    tau_syn_ms: float
    t_delay_ms: float
    w_syn_mV: float


def load_params(path: str | Path = "configs/lif_params.yaml") -> LIFParams:
    cfg = yaml.safe_load(Path(path).read_text())
    return LIFParams(
        dt_ms=cfg["dt_ms"],
        v_rest_mV=cfg["neuron"]["v_rest_mV"],
        v_reset_mV=cfg["neuron"]["v_reset_mV"],
        v_thresh_mV=cfg["neuron"]["v_thresh_mV"],
        tau_mem_ms=cfg["neuron"]["tau_mem_ms"],
        t_refrac_ms=cfg["neuron"]["t_refrac_ms"],
        tau_syn_ms=cfg["synapse"]["tau_syn_ms"],
        t_delay_ms=cfg["synapse"]["t_delay_ms"],
        w_syn_mV=cfg["synapse"]["w_syn_mV"],
    )


def transmitter_sign(transmitter: str) -> int:
    """+1 for acetylcholine, -1 for GABA and glutamate. Anything else is an error, not a guess."""
    try:
        return TRANSMITTER_SIGN[transmitter]
    except KeyError:
        raise ValueError(f"no sign rule for transmitter {transmitter!r}") from None


def synaptic_matrix(
    node_ids: list[int],
    pre: list[int],
    post: list[int],
    syn_count: list[int],
    transmitter: list[str],
    scale_mV: float,
) -> np.ndarray:
    """Weight matrix W[post, pre] in mV: sign(transmitter) x synapse count x scale."""
    index = {n: i for i, n in enumerate(node_ids)}
    w = np.zeros((len(node_ids), len(node_ids)))
    for a, b, count, nt in zip(pre, post, syn_count, transmitter, strict=True):
        w[index[b], index[a]] += transmitter_sign(nt) * count * scale_mV
    return w


class LIFNetwork:
    """State and update rule. step() advances one dt and returns the boolean spike vector."""

    def __init__(self, w: np.ndarray, params: LIFParams):
        if w.ndim != 2 or w.shape[0] != w.shape[1]:
            raise ValueError("w must be a square matrix [post, pre]")
        self.w, self.p, self.n = w, params, w.shape[0]
        self.refrac_steps = round(params.t_refrac_ms / params.dt_ms)
        self.delay_steps = max(1, round(params.t_delay_ms / params.dt_ms))
        self.reset()

    def reset(self) -> None:
        self.v = np.full(self.n, self.p.v_rest_mV)
        self.g = np.zeros(self.n)
        self.refrac = np.zeros(self.n, dtype=int)  # steps of refractoriness left
        self.pending = np.zeros((self.delay_steps, self.n))  # synaptic input still in transit
        self.t_step = 0

    def step(self, i_ext_mV: np.ndarray | float = 0.0) -> np.ndarray:
        p = self.p
        slot = self.t_step % self.delay_steps
        self.g += self.pending[slot]  # input that arrives now (applies even while refractory)
        self.pending[slot] = 0.0
        active = self.refrac == 0
        dv = (p.v_rest_mV - self.v + self.g + i_ext_mV) * (p.dt_ms / p.tau_mem_ms)
        self.v = np.where(active, self.v + dv, self.v)
        self.g = np.where(active, self.g * (1 - p.dt_ms / p.tau_syn_ms), self.g)
        self.refrac = np.maximum(self.refrac - 1, 0)
        spikes = active & (self.v > p.v_thresh_mV)
        if spikes.any():
            self.v[spikes] = p.v_reset_mV
            self.g[spikes] = 0.0
            self.refrac[spikes] = self.refrac_steps
            # the slot just read is free again, so it now holds input due delay_steps from now
            self.pending[slot] += self.w[:, spikes].sum(axis=1)
        self.t_step += 1
        return spikes


@dataclass
class SpikeRecord:
    """Every spike as (time in ms, neuron index). Saved and loaded without loss."""

    dt_ms: float
    n_neurons: int
    steps: list[int]
    neurons: list[int]

    @classmethod
    def empty(cls, n_neurons: int, dt_ms: float) -> SpikeRecord:
        return cls(dt_ms=dt_ms, n_neurons=n_neurons, steps=[], neurons=[])

    def add(self, step: int, spikes: np.ndarray) -> None:
        idx = np.flatnonzero(spikes)
        self.steps.extend([step] * len(idx))
        self.neurons.extend(idx.tolist())

    @property
    def times_ms(self) -> np.ndarray:
        return np.asarray(self.steps) * self.dt_ms

    def counts(self) -> np.ndarray:
        return np.bincount(self.neurons, minlength=self.n_neurons)

    def first_spike_ms(self, neuron: int) -> float | None:
        hits = [s for s, n in zip(self.steps, self.neurons, strict=True) if n == neuron]
        return min(hits) * self.dt_ms if hits else None

    def save(self, path: str | Path) -> None:
        np.savez(
            path,
            dt_ms=self.dt_ms,
            n_neurons=self.n_neurons,
            steps=np.asarray(self.steps, dtype=np.int64),
            neurons=np.asarray(self.neurons, dtype=np.int64),
        )

    @classmethod
    def load(cls, path: str | Path) -> SpikeRecord:
        d = np.load(path)
        return cls(
            dt_ms=float(d["dt_ms"]),
            n_neurons=int(d["n_neurons"]),
            steps=d["steps"].tolist(),
            neurons=d["neurons"].tolist(),
        )


def run_network(net: LIFNetwork, n_steps: int, schedule=None, watch: list[int] | None = None):
    """Run from a fresh state for n_steps. Returns (SpikeRecord, voltage trace of `watch` neurons).

    schedule: None (no input), an array [n_steps, n_neurons] of i_ext in mV, or a function
    step -> array [n_neurons] (or a scalar).
    """
    net.reset()
    record = SpikeRecord.empty(net.n, net.p.dt_ms)
    volts = np.zeros((n_steps, len(watch))) if watch else None
    for k in range(n_steps):
        i_ext = 0.0 if schedule is None else (schedule(k) if callable(schedule) else schedule[k])
        record.add(k, net.step(i_ext))
        if watch:
            volts[k] = net.v[watch]
    return record, volts


def run_graph(
    node_ids: list[int],
    edges: dict,
    scale_mV: float,
    n_steps: int,
    schedule=None,
    params: LIFParams | None = None,
    watch: list[int] | None = None,
):
    """Build a network from a graph and run it. edges has keys pre, post, syn_count, transmitter."""
    params = params or load_params()
    w = synaptic_matrix(
        node_ids,
        edges["pre"],
        edges["post"],
        edges["syn_count"],
        edges["transmitter"],
        scale_mV,
    )
    return run_network(LIFNetwork(w, params), n_steps, schedule, watch)
