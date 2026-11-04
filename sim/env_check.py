"""Phase 1C smoke test: can the simulator run headless and render a camera frame?

Run from the project root:  .venv/bin/python sim/env_check.py | tee logs/env_check.txt
No drone logic here; this only proves the tools work.
"""

import importlib.metadata as md
import platform
import sys

import numpy as np
import torch
from gym_pybullet_drones.envs.CtrlAviary import CtrlAviary
from gym_pybullet_drones.utils.enums import DroneModel, Physics


def main() -> int:
    print("== versions")
    print("python               ", platform.python_version())
    print("platform             ", platform.platform())
    for pkg in ("numpy", "pybullet", "torch", "gym-pybullet-drones", "gymnasium", "pytest"):
        print(f"{pkg:21}", md.version(pkg))
    print("torch cuda available ", torch.cuda.is_available())

    print("== one headless step")
    env = CtrlAviary(
        drone_model=DroneModel.CF2X,
        num_drones=1,
        physics=Physics.PYB,
        gui=False,
        record=False,
        user_debug_gui=False,
    )
    try:
        obs, _info = env.reset(seed=0)
        print("obs shape            ", np.asarray(obs).shape)
        hover_rpm = np.array([[env.HOVER_RPM] * 4])
        obs, _reward, terminated, truncated, _info = env.step(hover_rpm)
        print(f"stepped              ok  (terminated={terminated}, truncated={truncated})")
        z = float(np.asarray(obs)[0][2])
        print("drone z after step   ", round(z, 4))

        print("== one headless camera frame")
        # CtrlAviary does not allocate camera settings; the library camera is a fixed
        # 60-degree square-aspect view, so we set a square resolution ourselves.
        env.IMG_RES = np.array([128, 128])
        rgb, _depth, _seg = env._getDroneImages(0)
        rgb = np.asarray(rgb)
        print("rgb frame shape      ", rgb.shape, rgb.dtype)
        print("rgb frame min/max    ", int(rgb.min()), int(rgb.max()))
    finally:
        env.close()

    print("== result: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
