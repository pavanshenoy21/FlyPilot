"""Fixed visual front end of the fly pipeline. No learned parameters (locked decision 8).

5.2  coarse_grid: average the camera frame down to a fly-like grid of "ommatidia".
5.3  reichardt: a Hassenstein-Reichardt motion detector on that grid, split into ON (brightening)
     and OFF (darkening) channels like the fly's T4 and T5 cells.

Grid choice: a fruit fly's eye samples space about every 5 degrees (inter-ommatidial angle,
roughly 4.5-5 degrees; value from memory of the literature, citation still to be added to the
report). Over the simulator's 60 degree field of view that is 12 x 12 samples.
Declared simplification: the camera's pixels are not exactly equal in angle (a pinhole image
stretches towards the edges, by about 25% at 30 degrees), and we treat the 12 x 12 cells as equal.
"""

from __future__ import annotations

import numpy as np

GRID = 12  # cells per side: 60 degrees / 5 degrees
CELL_DEG = 5.0


def averaging_matrix(n_in: int, n_out: int) -> np.ndarray:
    """A [n_out, n_in] matrix whose rows average n_in/n_out input pixels, with partial pixels
    weighted by how much of them falls in the cell. Each row sums to 1."""
    edges = np.linspace(0, n_in, n_out + 1)
    a = np.zeros((n_out, n_in))
    for i in range(n_out):
        lo, hi = edges[i], edges[i + 1]
        for j in range(int(np.floor(lo)), int(np.ceil(hi))):
            a[i, j] = min(hi, j + 1) - max(lo, j)
    return a / a.sum(axis=1, keepdims=True)


def coarse_grid(frames: np.ndarray, n: int = GRID) -> np.ndarray:
    """Area-average [..., H, W] frames down to [..., n, n]. The mean intensity is preserved."""
    h, w = frames.shape[-2:]
    rows, cols = averaging_matrix(h, n), averaging_matrix(w, n)
    return np.einsum("ih,...hw,jw->...ij", rows, frames.astype(np.float64), cols).astype(np.float32)


# ---- 5.3 Reichardt motion detector ----

FPS = 30.0
TAU_DELAY_MS = 50.0  # delay-arm low-pass filter. Chosen (about 1.5 frames), not fitted, not cited.
DIRECTIONS = ("right", "left", "down", "up")  # image directions; "down" = increasing row
POLARITIES = ("on", "off")


def on_off(grid: np.ndarray) -> np.ndarray:
    """Frame-to-frame change split into ON and OFF: [T, n, n] -> [T, 2, n, n], both >= 0.
    The first frame has no previous frame, so its change is zero."""
    diff = np.diff(grid, axis=0, prepend=grid[:1])
    return np.stack([np.maximum(diff, 0), np.maximum(-diff, 0)], axis=1)


def low_pass(x: np.ndarray, tau_ms: float = TAU_DELAY_MS, fps: float = FPS) -> np.ndarray:
    """First-order low-pass filter along time (axis 0), starting from zero."""
    a = np.exp(-1000.0 / (fps * tau_ms))
    out = np.zeros_like(x)
    for t in range(len(x)):
        out[t] = (a * out[t - 1] if t else 0) + (1 - a) * x[t]
    return out


def reichardt(grid: np.ndarray, tau_ms: float = TAU_DELAY_MS, fps: float = FPS) -> np.ndarray:
    """Motion energy from grid frames [T, n, n] -> [T, 2 polarities, 4 directions, n, n].

    For each neighbouring pair of cells (a, b), with a the left (or upper) one:
        R = delayed(a) * b - a * delayed(b)     (positive when motion goes from a to b)
    computed separately in the ON and OFF channels. Positive R counts as "right" (or "down"),
    negative R as "left" (or "up"). Each pair's value is stored at cell a; the last column
    (or row) has no right (or lower) neighbour and stays zero.
    """
    c = on_off(grid.astype(np.float64))
    d = low_pass(c, tau_ms, fps)
    h = d[..., :, :-1] * c[..., :, 1:] - c[..., :, :-1] * d[..., :, 1:]
    v = d[..., :-1, :] * c[..., 1:, :] - c[..., :-1, :] * d[..., 1:, :]
    t, n = grid.shape[0], grid.shape[-1]
    out = np.zeros((t, 2, 4, n, n))
    out[:, :, 0, :, :-1] = np.maximum(h, 0)
    out[:, :, 1, :, :-1] = np.maximum(-h, 0)
    out[:, :, 2, :-1, :] = np.maximum(v, 0)
    out[:, :, 3, :-1, :] = np.maximum(-v, 0)
    return out.astype(np.float32)
