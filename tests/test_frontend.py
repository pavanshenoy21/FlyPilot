"""Tests for fly/frontend.py (Phase 5.2 coarse grid, 5.3 Reichardt motion detector)."""

import numpy as np
import pytest

from fly.frontend import (
    DIRECTIONS,
    GRID,
    averaging_matrix,
    coarse_grid,
    low_pass,
    on_off,
    reichardt,
)
from sim import stimuli as st


def test_output_shape_for_a_frame_and_a_stack():
    assert coarse_grid(np.zeros((128, 128))).shape == (GRID, GRID)
    assert coarse_grid(np.zeros((7, 128, 128))).shape == (7, GRID, GRID)


def test_each_row_of_the_averaging_matrix_sums_to_one():
    a = averaging_matrix(128, 12)
    assert a.shape == (12, 128) and np.allclose(a.sum(axis=1), 1.0)


def test_mean_intensity_is_preserved():
    rng = np.random.default_rng(0)
    frame = rng.random((128, 128)).astype(np.float32)
    assert coarse_grid(frame).mean() == pytest.approx(frame.mean(), abs=1e-6)


def test_constant_image_stays_constant():
    assert np.allclose(coarse_grid(np.full((128, 128), 0.4)), 0.4)


def test_matches_plain_block_average_when_sizes_divide_evenly():
    frame = np.random.default_rng(1).random((128, 128))
    blocks = frame.reshape(16, 8, 16, 8).mean(axis=(1, 3))  # 8 x 8 pixel blocks
    assert np.allclose(coarse_grid(frame, n=16), blocks, atol=1e-6)


def test_a_dark_square_lands_in_the_right_cell():
    frame = np.ones((128, 128))
    frame[0:10, 118:128] = 0.0  # top right corner
    g = coarse_grid(frame)
    assert g[0, -1] == g.min() and g[-1, 0] == pytest.approx(1.0)


def test_a_small_looming_dot_covers_more_of_the_grid_as_it_grows():
    s = st.make_looming(0.2, 3.0, 2.0)
    g = coarse_grid(s.frames)
    darkness = (st.BACKGROUND - g).sum(axis=(1, 2))  # total darkness is conserved by averaging
    assert np.all(np.diff(darkness) > -1e-4)  # grows (until the dot leaves the frame)
    assert darkness[-1] > 5 * darkness[0]


def test_no_learned_parameters():
    # the downsampler is a fixed linear map: same input, same output, and linear in the input
    a, b = np.random.default_rng(2).random((2, 128, 128))
    assert np.allclose(coarse_grid(a + 2 * b), coarse_grid(a) + 2 * coarse_grid(b), atol=1e-5)


# ---- 5.3 Reichardt motion detector ----


def energy(frames: np.ndarray) -> np.ndarray:
    """Total motion energy per [polarity, direction]."""
    return reichardt(coarse_grid(frames)).sum(axis=(0, 3, 4))


@pytest.mark.parametrize("direction", DIRECTIONS)
@pytest.mark.parametrize("dark", [True, False])
def test_moving_bar_gives_the_right_direction_in_both_channels(direction, dark):
    e = energy(st.moving_bar(direction, dark=dark))
    k = DIRECTIONS.index(direction)
    for pol in range(2):  # a bar has a darkening edge and a brightening edge
        assert e[pol].argmax() == k
        opposite = {0: 1, 1: 0, 2: 3, 3: 2}[k]
        assert e[pol, k] > 5 * e[pol, opposite]


def test_static_image_gives_no_motion():
    frames = np.repeat(st.make_looming(0.2, 3.0, 2.0).frames[:1], 20, axis=0)
    assert np.all(reichardt(coarse_grid(frames)) == 0)


def test_full_field_flicker_gives_no_net_direction():
    levels = np.array([0.2, 0.8] * 10)
    frames = np.repeat(levels[:, None, None], 128, 1).repeat(128, 2)
    assert np.allclose(reichardt(coarse_grid(frames)), 0, atol=1e-7)


def test_on_off_split():
    g = np.array([0.5, 0.7, 0.4])[:, None, None] * np.ones((3, 2, 2))
    c = on_off(g)
    assert np.allclose(c[1, 0], 0.2) and np.allclose(c[1, 1], 0)  # brightening -> ON
    assert np.allclose(c[2, 1], 0.3) and np.allclose(c[2, 0], 0)  # darkening -> OFF
    assert np.all(c[0] == 0)


def test_low_pass_step_response():
    x = np.ones((60, 1))
    y = low_pass(x, tau_ms=50.0, fps=30.0)
    a = np.exp(-1000 / (30 * 50))
    assert y[0, 0] == pytest.approx(1 - a) and y[-1, 0] == pytest.approx(1.0, abs=1e-6)


def test_looming_dot_moves_outward():
    # a centred looming dot expands: rightward motion on the right half, leftward on the left
    s = st.make_looming(0.15, 2.0, 2.0)
    m = reichardt(coarse_grid(s.frames)).sum(axis=(0, 1))  # [direction, n, n]
    half = m.shape[-1] // 2
    right, left, down, up = m
    assert right[:, half:].sum() > 3 * left[:, half:].sum()
    assert left[:, :half].sum() > 3 * right[:, :half].sum()
    assert down[half:, :].sum() > 3 * up[half:, :].sum()
    assert up[:half, :].sum() > 3 * down[:half, :].sum()


def test_bar_with_frames_shuffled_in_time_has_no_clear_direction():
    # control: direction must come from the order of frames, not from the bar's shape
    f = st.moving_bar("right")
    f = f[np.random.default_rng(0).permutation(len(f))]
    e = energy(f)
    for pol in range(2):
        assert 0.5 < e[pol, 0] / e[pol, 1] < 2.0
