"""Tests for fly/circuit.py (Phase 6.1): the assembled circuit, end to end."""

import numpy as np
import pytest

from fly import circuit as fc
from fly.frontend import GRID
from sim import stimuli as st


@pytest.fixture(scope="module")
def circuit():
    return fc.load_circuit()


def test_circuit_has_all_neurons_and_both_giant_fibers(circuit):
    assert len(circuit.node_ids) == 295 and len(circuit.source_idx) == 293
    assert set(circuit.gf_idx) == {"left", "right"}
    assert circuit.kernels.shape == (293, 4, GRID, GRID)


def test_weights_are_published_synapse_weight_times_count(circuit):
    # every edge is excitatory (decisions_log 13); total synapses as in the subgraph
    assert circuit.counts.min() >= 0 and circuit.counts.sum() == 1885
    assert circuit.params.w_syn_mV == 0.275


def test_lplc2_kernel_is_outward_minus_inward_and_lc4_outward_only():
    k = fc.kernels_for(np.array([6.0, 6.0]), np.array([6.0, 6.0]), np.array(["LPLC2", "LC4"]), 2.0)
    lp, lc = k
    # right of centre: rightward motion is outward (+), leftward is inward (- for LPLC2, 0 for LC4)
    assert lp[0, 6, 7] > 0 and lp[1, 6, 7] < 0
    assert lc[0, 6, 7] > 0 and lc[1, 6, 7] == 0
    assert lp[0, 6, 4] < 0 and lp[1, 6, 4] > 0  # left of centre: the reverse
    assert np.isclose(
        np.abs(lc).sum(axis=0).max() * (np.abs(lc).sum(axis=0) > 0).sum(), 2.0, atol=1
    )


def test_no_motion_means_no_spikes(circuit):
    frames = np.repeat(st.make_looming(0.2, 3.0, 2.0).frames[:1], 10, axis=0)
    r = fc.run(circuit, frames, input_gain=10.0)
    assert r.source_spikes == 0 and r.trigger_ms is None


def test_end_to_end_looming_from_the_left_triggers_the_left_giant_fiber(circuit):
    s = st.make_looming(0.25, 3.0, 1.5, x_m=-0.15)  # object left of centre
    r = fc.run(circuit, s.frames, input_gain=10.0)
    assert r.trigger_ms is not None
    assert r.threat_side == "left"  # so the drone dodges right
    assert r.trigger_ms / 1000 < s.ttc_s[0]  # fires before impact


def test_mirror_stimulus_triggers_the_right_giant_fiber(circuit):
    s = st.make_looming(0.25, 3.0, 1.5, x_m=0.15)
    assert fc.run(circuit, s.frames, input_gain=10.0).threat_side == "right"


def test_passing_object_does_not_trigger_at_the_same_gain(circuit):
    s = st.make_passing(0.25, 2.0, 2.0)
    assert fc.run(circuit, s.frames, input_gain=10.0).trigger_ms is None


def test_flip_horizontal_keeps_each_eye_in_its_half():
    # regression: a left-eye neuron exactly on the centre line (column 6.0) used to be sent to the
    # far right edge, because the flip chose the eye from the column instead of the neuron's side
    a, b = fc.load_circuit(), fc.load_circuit(flip_horizontal=True)
    assert not np.allclose(a.kernels, b.kernels)
    left = [i for i, n in enumerate(a.source_idx) if a.side[n] == "left"]
    assert (
        b.kernels[left][:, :, :, GRID // 2 + 2 :].any()
        == a.kernels[left][:, :, :, GRID // 2 + 2 :].any()
    )
