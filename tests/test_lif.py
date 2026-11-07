"""Tests for fly/lif.py (Phase 4A): neuron update, signed synapses, delay."""

import math

import numpy as np
import pytest

from fly.lif import LIFNetwork, load_params, synaptic_matrix, transmitter_sign

P = load_params()


def single(i_ext: float, ms: float) -> np.ndarray:
    net = LIFNetwork(np.zeros((1, 1)), P)
    n = round(ms / P.dt_ms)
    return np.array([net.step(i_ext)[0] for _ in range(n)])


def test_params_match_the_published_source():
    assert (P.v_rest_mV, P.v_thresh_mV, P.tau_mem_ms) == (-52.0, -45.0, 20.0)
    assert (P.tau_syn_ms, P.t_refrac_ms, P.t_delay_ms, P.w_syn_mV) == (5.0, 2.2, 1.8, 0.275)


def test_constant_input_fires_at_the_analytic_rate():
    drive = 10.0  # mV above rest
    gap = P.v_thresh_mV - P.v_rest_mV
    to_threshold = P.tau_mem_ms * math.log(drive / (drive - gap))
    expected_hz = 1000.0 / (to_threshold + P.t_refrac_ms)
    spikes = single(drive, 2000.0)
    measured_hz = spikes.sum() / 2.0
    assert measured_hz == pytest.approx(expected_hz, rel=0.05)


def test_input_below_threshold_never_fires():
    assert single(6.0, 1000.0).sum() == 0  # steady state is 6 mV above rest, threshold is 7


def test_no_two_spikes_closer_than_the_refractory_period():
    times = np.flatnonzero(single(20.0, 500.0)) * P.dt_ms
    assert len(times) > 5
    assert np.diff(times).min() >= P.t_refrac_ms - 1e-9


def test_sign_follows_the_transmitter():
    assert transmitter_sign("acetylcholine") == 1
    assert transmitter_sign("gaba") == -1
    assert transmitter_sign("glutamate") == -1
    with pytest.raises(ValueError):
        transmitter_sign("serotonin")


def test_weight_is_sign_times_count_times_scale():
    ids = [1, 2, 3]
    w = synaptic_matrix(ids, [1, 1], [2, 3], [4, 4], ["acetylcholine", "gaba"], scale_mV=0.5)
    assert w[1, 0] == 2.0 and w[2, 0] == -2.0  # [post, pre]
    w2 = synaptic_matrix(ids, [1], [2], [8], ["acetylcholine"], scale_mV=0.5)
    assert w2[1, 0] == 4.0  # doubling the count doubles the weight


def pair(transmitter: str, count: int = 3):
    w = synaptic_matrix([1, 2], [1], [2], [count], [transmitter], scale_mV=P.w_syn_mV)
    return LIFNetwork(w, P)


def test_excitatory_synapse_depolarises_and_inhibitory_hyperpolarises_the_target():
    for nt, direction in (("acetylcholine", 1), ("gaba", -1)):
        net = pair(nt, count=20)
        for _ in range(60):  # drive neuron 0 only, until it has fired
            net.step(np.array([30.0, 0.0]))
        peak = 0.0
        for _ in range(100):
            net.step(np.array([0.0, 0.0]))
            peak = max(peak, direction * (net.v[1] - P.v_rest_mV))
        assert peak > 0.05


def test_synaptic_input_arrives_exactly_one_delay_later():
    net = pair("acetylcholine")
    fired_at = arrived_at = None
    for k in range(200):
        s = net.step(np.array([30.0, 0.0]))
        if fired_at is None and s[0]:
            fired_at = k
        if fired_at is not None and arrived_at is None and net.g[1] > 0:
            arrived_at = k
    assert arrived_at - fired_at == round(P.t_delay_ms / P.dt_ms)


def test_reset_restores_the_initial_state():
    net = pair("acetylcholine")
    for _ in range(100):
        net.step(np.array([30.0, 0.0]))
    net.reset()
    assert np.all(net.v == P.v_rest_mV) and np.all(net.g == 0) and net.t_step == 0
