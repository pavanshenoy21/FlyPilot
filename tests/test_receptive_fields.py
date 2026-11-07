"""Tests for fly/receptive_fields.py (Phase 5.4) on a synthetic lobula sheet with known layout."""

import numpy as np
import pandas as pd
import pytest

from fly import receptive_fields as rf


def sheet(n: int = 200, seed: int = 0):
    """Points on a tilted sheet. dv = dorsal-ventral position, ap = anterior-posterior position."""
    rng = np.random.default_rng(seed)
    dv, ap = rng.uniform(-1, 1, n), rng.uniform(-1, 1, n)
    y = 60 * dv  # FlyWire y grows ventrally, so +dv is ventral
    z = 40 * ap  # z grows posteriorly
    x = 10 * ap + rng.normal(0, 1, n)  # tilt plus a little thickness
    return np.stack([x, y, z], axis=1), dv, ap


def corr(a, b):
    return np.corrcoef(a, b)[0, 1]


def test_sheet_normal_is_the_thin_direction():
    xyz, _, _ = sheet()
    up, back, normal = rf.sheet_axes(xyz)
    for v in (up, back, normal):
        assert np.linalg.norm(v) == pytest.approx(1)
    assert abs(up @ normal) < 1e-9 and abs(back @ normal) < 1e-9 and abs(up @ back) < 1e-9
    assert up[1] < 0 and back[2] > 0  # up is dorsal, back is posterior


def test_ventral_maps_down_and_posterior_maps_outward():
    xyz, dv, ap = sheet()
    left = rf.map_side(xyz, "left")
    right = rf.map_side(xyz, "right")
    assert corr(left[:, 0], dv) > 0.95  # row grows ventrally
    assert corr(left[:, 1], ap) < -0.95  # left eye: posterior -> left edge (small column)
    assert corr(right[:, 1], ap) > 0.95  # right eye: posterior -> right edge


def test_each_eye_stays_in_its_half_and_fills_it():
    xyz, _, _ = sheet()
    left, right = rf.map_side(xyz, "left"), rf.map_side(xyz, "right")
    assert left[:, 1].min() >= 0 and left[:, 1].max() <= rf.GRID / 2
    assert right[:, 1].min() >= rf.GRID / 2 and right[:, 1].max() <= rf.GRID
    assert np.ptp(left[:, 0]) > 0.9 * rf.GRID and np.ptp(left[:, 1]) > 0.9 * rf.GRID / 2


def test_left_and_right_are_mirror_images():
    xyz, _, _ = sheet()
    left, right = rf.map_side(xyz, "left"), rf.map_side(xyz, "right")
    assert np.allclose(left[:, 0], right[:, 0])
    assert np.allclose(left[:, 1], rf.GRID - right[:, 1])


def test_flip_horizontal_mirrors_within_the_eye():
    xyz, _, _ = sheet()
    a, b = rf.map_side(xyz, "left"), rf.map_side(xyz, "left", flip_horizontal=True)
    assert np.allclose(a[:, 0], b[:, 0])
    assert np.allclose(a[:, 1] + b[:, 1], rf.GRID / 2)


def test_build_gives_angles_consistent_with_grid():
    xyz, _, _ = sheet(50)
    rows = []
    for side in ("left", "right"):
        for i, (x, y, z) in enumerate(xyz):
            rows.append((i if side == "left" else 1000 + i, "LO", 5, x, y, z, "LPLC2", side))
    cen = pd.DataFrame(
        rows, columns=["root_id", "layer", "n_sites", "cx", "cy", "cz", "cell_type", "side"]
    )
    out = rf.build(cen)
    assert len(out) == 100
    assert (out[out.side == "left"].azimuth_deg <= 0).all()
    assert (out[out.side == "right"].azimuth_deg >= 0).all()
    assert out.elevation_deg.between(-30, 30).all()
