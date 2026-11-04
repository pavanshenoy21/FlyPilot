"""Environment sanity tests (Phase 1D).

These guard against the toolchain drifting: wrong Python, a missing package, or a
simulator that no longer runs headless. They contain no project science.
"""

import sys


def test_python_version_is_3_12():
    assert sys.version_info[:2] == (3, 12)


def test_core_packages_import():
    import gym_pybullet_drones  # noqa: F401
    import numpy  # noqa: F401
    import pybullet  # noqa: F401
    import torch  # noqa: F401
    import yaml  # noqa: F401


def test_simulator_runs_one_headless_step():
    import numpy as np
    from gym_pybullet_drones.envs.CtrlAviary import CtrlAviary
    from gym_pybullet_drones.utils.enums import DroneModel, Physics

    env = CtrlAviary(
        drone_model=DroneModel.CF2X,
        num_drones=1,
        physics=Physics.PYB,
        gui=False,
        record=False,
        user_debug_gui=False,
    )
    try:
        env.reset(seed=0)
        obs, _reward, terminated, truncated, _info = env.step(np.array([[env.HOVER_RPM] * 4]))
        assert np.asarray(obs).shape == (1, 20)
        assert not terminated and not truncated
    finally:
        env.close()
