"""Two figures for the Phase I pitch, both made from real data or the real simulator.

1. circuit_subgraph.png : the LPLC2 / LC4 -> giant fiber wiring from FlyWire snapshot 783
                          (reads connectome/data/subgraph_v783/edges.csv).
2. looming_frames.png   : what the simulated drone's camera sees as an object approaches
                          (gym-pybullet-drones; the object grows in the view = looming).

Run from the project root:  .venv/bin/python demo/pitch_figures.py
Nothing here is a result: no circuit is simulated and nothing is trained.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OUT = Path("notebooks/figures")
EDGES = Path("connectome/data/subgraph_v783/edges.csv")
NAVY, MAROON, GREY = "#002060", "#C00000", "#595959"


def circuit_figure() -> Path:
    e = pd.read_csv(EDGES)
    fig, axes = plt.subplots(1, 2, figsize=(13, 6.2))
    for ax, side in zip(axes, ["left", "right"], strict=True):
        sub = e[e.post_side == side]
        ax.set_xlim(-0.05, 1.12)
        ax.set_ylim(-0.12, 1.1)
        ax.axis("off")
        gf = (1.0, 0.5)
        ax.scatter(*gf, s=1500, color="#E8A400", edgecolor="black", zorder=5)
        ax.text(gf[0], gf[1] - 0.11, f"giant fiber\n({side})", ha="center", va="top", fontsize=16)
        for cell_type, y0, color in (("LPLC2", 0.86, NAVY), ("LC4", 0.14, MAROON)):
            grp = sub[sub.pre_type == cell_type].sort_values("syn_count", ascending=False)
            xs = np.linspace(0.02, 0.62, len(grp))
            ys = np.full(len(grp), y0)
            for x, y, syn in zip(xs, ys, grp.syn_count, strict=True):
                ax.plot([x, gf[0]], [y, gf[1]], color=color, alpha=0.18, lw=0.3 + 0.22 * syn)
            ax.scatter(xs, ys, s=22, color=color, zorder=4)
            n_syn = int(grp.syn_count.sum())
            ax.text(
                0.02,
                y0 + (0.07 if cell_type == "LPLC2" else -0.08),
                f"{cell_type}: {len(grp)} neurons, {n_syn} synapses",
                color=color,
                fontsize=17,
                fontweight="bold",
                va="center",
            )
        ax.set_title(f"{side.capitalize()} side", fontsize=18, color=GREY)
    fig.suptitle(
        "Each dot is one neuron. Line thickness = number of synapses. Every connection stays on its own side.",
        fontsize=15,
    )
    fig.text(
        0.5,
        0.01,
        "LPLC2 + LC4 supply about 20% of each giant fiber's input; the rest comes from other cell types.",
        ha="center",
        fontsize=14,
        color=GREY,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.93))
    path = OUT / "circuit_subgraph.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def looming_figure() -> Path:
    import pybullet as p
    import pybullet_data
    from gym_pybullet_drones.envs.CtrlAviary import CtrlAviary
    from gym_pybullet_drones.utils.enums import DroneModel, Physics

    env = CtrlAviary(
        drone_model=DroneModel.CF2X,
        num_drones=1,
        physics=Physics.PYB,
        initial_xyzs=np.array([[0.0, 0.0, 1.0]]),
        gui=False,
        record=False,
        user_debug_gui=False,
    )
    try:
        env.reset(seed=0)
        env.IMG_RES = np.array([256, 256])
        p.setAdditionalSearchPath(pybullet_data.getDataPath(), physicsClientId=env.CLIENT)
        radius = 0.25  # the sphere2 model has radius 0.5 at scale 1
        ball = p.loadURDF(
            "sphere2red.urdf",
            basePosition=[3.0, 0.0, 1.0],
            globalScaling=2 * radius,
            useFixedBase=True,
            physicsClientId=env.CLIENT,
        )
        distances = [4.0, 2.5, 1.5, 0.9]
        frames = []
        for d in distances:
            p.resetBasePositionAndOrientation(
                ball, [d, 0.0, 1.0], [0, 0, 0, 1], physicsClientId=env.CLIENT
            )
            rgb, _depth, seg = env._getDroneImages(0, segmentation=True)
            frames.append((np.asarray(rgb)[..., :3].astype(np.uint8), np.asarray(seg)))
    finally:
        env.close()

    fig, axes = plt.subplots(1, len(frames), figsize=(14, 4.6))
    for ax, d, (rgb, seg) in zip(axes, distances, frames, strict=True):
        ax.imshow(rgb)
        ax.axis("off")
        pix = int(((seg & 0xFFFFFF) == ball).sum())
        ax.set_title(f"object {d:.1f} m away\ncovers {pix} pixels", fontsize=18)
    fig.suptitle(
        "The object grows faster and faster as it approaches: this is looming",
        fontsize=17,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    path = OUT / "looming_frames.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("wrote", circuit_figure())
    print("wrote", looming_figure())


if __name__ == "__main__":
    main()
