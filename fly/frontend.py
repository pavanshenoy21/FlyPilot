"""Fixed visual front end of the fly pipeline. No learned parameters (locked decision 8).

5.2  coarse_grid: average the camera frame down to a fly-like grid of "ommatidia".
5.3  (next) a Reichardt-style motion detector on that grid.

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
