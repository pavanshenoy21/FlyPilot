"""Synthetic stimuli for the fly front end (Phase 5.1): looming, passing and receding dots.

A dark sphere on a bright background, seen by a pinhole camera with the simulator's settings
(60 degree field of view, square frames, 30 fps). The camera looks along +z. Everything is
analytic, so the time to collision (TTC) of every frame is known exactly.

    looming   moves straight towards the camera (z shrinks), offset sideways by (x, y) metres
    passing   crosses the view sideways at constant distance (constant size)
    receding  moves straight away (z grows)

Impact = the sphere's nearest surface point reaches the camera plane, i.e. z - radius = 0, so
    TTC(t) = (z(t) - radius) / speed        for looming, and undefined (nan) otherwise.
The sphere's outline is drawn as a disc of radius f * R / sqrt(z^2 - R^2) pixels (exact for a
sphere on the optical axis, a small approximation when it is off-axis). Edges are anti-aliased.

Run from the project root to save a contact sheet:   .venv/bin/python -m sim.stimuli
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

FOV_DEG = 60.0  # same as the simulator camera
FPS = 30.0
SIZE = 128  # pixels per side (the simulator's frame size)
BACKGROUND, OBJECT = 0.85, 0.10  # grey levels, 0 = black

KINDS = ("looming", "passing", "receding")

# Ranges a random stimulus is drawn from (metres, seconds, metres per second).
RANGES = {
    "radius_m": (0.10, 0.40),
    "speed_mps": (1.5, 4.0),
    "duration_s": (1.5, 3.0),
    "offset_m": (-0.30, 0.30),  # sideways offset of a looming or receding object, per axis
    "pass_distance_m": (1.5, 4.0),
    "receding_start_m": (0.8, 2.0),
}


@dataclass(frozen=True)
class Stimulus:
    kind: str
    frames: np.ndarray  # [T, SIZE, SIZE] float32 in [0, 1]
    times_s: np.ndarray  # [T]
    ttc_s: np.ndarray  # [T] exact time to collision, nan unless looming
    radius_px: np.ndarray  # [T] disc radius in pixels
    centre_px: np.ndarray  # [T, 2] disc centre (column, row)
    params: dict


def focal_px(size: int = SIZE) -> float:
    return (size / 2) / np.tan(np.radians(FOV_DEG) / 2)


def render(centre_px: np.ndarray, radius_px: np.ndarray, size: int = SIZE) -> np.ndarray:
    """Anti-aliased dark discs on a bright background. Inputs have one row per frame."""
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32) + 0.5
    cx, cy = centre_px[:, 0, None, None], centre_px[:, 1, None, None]
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    coverage = np.clip(radius_px[:, None, None] + 0.5 - dist, 0.0, 1.0)
    return (BACKGROUND + (OBJECT - BACKGROUND) * coverage).astype(np.float32)


def _make(kind: str, pos: np.ndarray, radius_m: float, times: np.ndarray, ttc, params: dict):
    """pos is [T, 3] (x, y, z) of the sphere centre in camera coordinates."""
    f = focal_px()
    z = pos[:, 2]
    radius_px = f * radius_m / np.sqrt(z**2 - radius_m**2)
    centre = np.stack([SIZE / 2 + f * pos[:, 0] / z, SIZE / 2 + f * pos[:, 1] / z], axis=1)
    return Stimulus(
        kind=kind,
        frames=render(centre, radius_px),
        times_s=times,
        ttc_s=ttc,
        radius_px=radius_px,
        centre_px=centre,
        params=params,
    )


def _times(duration_s: float) -> np.ndarray:
    return np.arange(int(np.floor(duration_s * FPS))) / FPS


def make_looming(
    radius_m: float, speed_mps: float, impact_s: float, x_m: float = 0.0, y_m: float = 0.0
) -> Stimulus:
    """Impact happens at impact_s; the last frame is the last one before it."""
    t = _times(impact_s)
    ttc = impact_s - t
    z = radius_m + speed_mps * ttc  # surface reaches the camera when ttc = 0
    pos = np.stack([np.full_like(t, x_m), np.full_like(t, y_m), z], axis=1)
    p = {"radius_m": radius_m, "speed_mps": speed_mps, "impact_s": impact_s, "x_m": x_m, "y_m": y_m}
    return _make("looming", pos, radius_m, t, ttc, p)


def make_passing(
    radius_m: float, distance_m: float, duration_s: float, y_m: float = 0.0, direction: int = 1
) -> Stimulus:
    """Crosses the whole field of view at constant distance, so its size never changes."""
    t = _times(duration_s)
    half = distance_m * np.tan(np.radians(FOV_DEG) / 2) + radius_m
    x = direction * np.linspace(-half, half, len(t))
    pos = np.stack([x, np.full_like(t, y_m), np.full_like(t, distance_m)], axis=1)
    p = {"radius_m": radius_m, "distance_m": distance_m, "duration_s": duration_s, "y_m": y_m}
    p["direction"] = direction
    return _make("passing", pos, radius_m, t, np.full_like(t, np.nan), p)


def make_receding(
    radius_m: float, speed_mps: float, duration_s: float, start_m: float, x_m=0.0, y_m=0.0
) -> Stimulus:
    t = _times(duration_s)
    z = radius_m + start_m + speed_mps * t
    pos = np.stack([np.full_like(t, x_m), np.full_like(t, y_m), z], axis=1)
    p = {"radius_m": radius_m, "speed_mps": speed_mps, "duration_s": duration_s}
    p.update(start_m=start_m, x_m=x_m, y_m=y_m)
    return _make("receding", pos, radius_m, t, np.full_like(t, np.nan), p)


def make_stimulus(kind: str, seed: int) -> Stimulus:
    """A random stimulus of the given kind; the same seed always gives the same stimulus."""
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}")
    rng = np.random.default_rng(seed)
    u = {k: rng.uniform(*v) for k, v in RANGES.items()}
    if kind == "looming":
        x, y = rng.uniform(*RANGES["offset_m"], size=2)
        return make_looming(u["radius_m"], u["speed_mps"], u["duration_s"], x, y)
    if kind == "passing":
        direction = int(rng.choice([-1, 1]))
        y = rng.uniform(*RANGES["offset_m"])
        return make_passing(u["radius_m"], u["pass_distance_m"], u["duration_s"], y, direction)
    x, y = rng.uniform(*RANGES["offset_m"], size=2)
    return make_receding(
        u["radius_m"], u["speed_mps"], u["duration_s"], u["receding_start_m"], x, y
    )


def make_figure(path: str = "notebooks/figures/synthetic_stimuli.png") -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    stims = [make_stimulus(k, seed=1) for k in KINDS]
    fig, axes = plt.subplots(3, 5, figsize=(11, 7))
    for row, s in zip(axes, stims, strict=True):
        picks = np.linspace(0, len(s.frames) - 1, 5).astype(int)
        for ax, i in zip(row, picks, strict=True):
            ax.imshow(s.frames[i], cmap="gray", vmin=0, vmax=1)
            ax.set_xticks([])
            ax.set_yticks([])
            ttc = s.ttc_s[i]
            ax.set_title(f"t={s.times_s[i]:.2f}s" + ("" if np.isnan(ttc) else f"  TTC={ttc:.2f}s"))
        row[0].set_ylabel(s.kind, fontsize=12)
    fig.suptitle("Synthetic stimuli: a dark sphere looming, passing and receding", fontsize=13)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    print("wrote", path)


if __name__ == "__main__":
    make_figure()
