"""Tests for sim/stimuli.py (Phase 5.1): geometry and time to collision checked analytically."""

import numpy as np
import pytest

from sim import stimuli as st


def test_ttc_is_exact_and_counts_down_one_frame_at_a_time():
    s = st.make_looming(radius_m=0.2, speed_mps=3.0, impact_s=2.0)
    assert np.allclose(np.diff(s.ttc_s), -1 / st.FPS)
    assert s.ttc_s[0] == pytest.approx(2.0)
    assert 0 < s.ttc_s[-1] <= 1 / st.FPS + 1e-9  # last frame is the last one before impact


def test_ttc_matches_distance_over_speed():
    r, v = 0.25, 2.5
    s = st.make_looming(r, v, 2.4)
    # surface distance at each frame = z - r = v * ttc, and the size must follow from that z
    z = r + v * s.ttc_s
    assert np.allclose(s.radius_px, st.focal_px() * r / np.sqrt(z**2 - r**2))


def test_apparent_size_estimate_of_ttc_agrees_early_on():
    # classic looming result: for a small object, radius / (d radius / dt) is close to the TTC
    s = st.make_looming(0.1, 2.0, 2.5)
    rate = np.gradient(s.radius_px, s.times_s)
    tau = s.radius_px / rate
    early = slice(0, 20)
    assert np.allclose(tau[early], s.ttc_s[early], rtol=0.08)


def test_rendered_area_matches_the_disc():
    s = st.make_looming(0.2, 3.0, 2.0)
    i = 30
    dark = (st.BACKGROUND - s.frames[i]) / (st.BACKGROUND - st.OBJECT)  # 0..1 coverage
    assert dark.sum() == pytest.approx(np.pi * s.radius_px[i] ** 2, rel=0.03)


def test_passing_keeps_its_size_and_has_no_ttc():
    s = st.make_passing(0.2, 2.5, 2.0)
    assert np.allclose(s.radius_px, s.radius_px[0])
    assert np.all(np.isnan(s.ttc_s))
    assert s.centre_px[0, 0] < 0 and s.centre_px[-1, 0] > st.SIZE  # enters left, leaves right


def test_passing_direction_flips():
    a, b = st.make_passing(0.2, 2.5, 2.0, direction=1), st.make_passing(0.2, 2.5, 2.0, direction=-1)
    assert a.centre_px[0, 0] < 0 < st.SIZE < b.centre_px[0, 0]


def test_receding_shrinks_and_has_no_ttc():
    s = st.make_receding(0.2, 2.0, 2.0, start_m=1.0)
    assert np.all(np.diff(s.radius_px) < 0)
    assert np.all(np.isnan(s.ttc_s))


def test_looming_grows():
    s = st.make_looming(0.2, 3.0, 2.0)
    assert np.all(np.diff(s.radius_px) > 0)


def test_frames_shape_dtype_and_range():
    for kind in st.KINDS:
        s = st.make_stimulus(kind, 0)
        assert s.frames.shape == (len(s.times_s), st.SIZE, st.SIZE)
        assert s.frames.dtype == np.float32
        assert s.frames.min() >= 0 and s.frames.max() <= 1
        assert s.frames[0].max() == pytest.approx(st.BACKGROUND)  # background pixels exist


def test_same_seed_same_stimulus_and_different_seed_differs():
    a, b, c = (st.make_stimulus("looming", s) for s in (5, 5, 6))
    assert np.array_equal(a.frames, b.frames)
    assert a.params != c.params


def test_random_stimuli_stay_inside_the_ranges():
    for seed in range(20):
        s = st.make_stimulus("looming", seed)
        lo, hi = st.RANGES["radius_m"]
        assert lo <= s.params["radius_m"] <= hi
        assert s.ttc_s[0] <= st.RANGES["duration_s"][1]


def test_unknown_kind_is_rejected():
    with pytest.raises(ValueError):
        st.make_stimulus("sideways", 0)
