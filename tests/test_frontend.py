"""Tests for fly/frontend.py (Phase 5.2): the coarse grid downsampler."""

import numpy as np
import pytest

from fly.frontend import GRID, averaging_matrix, coarse_grid
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
