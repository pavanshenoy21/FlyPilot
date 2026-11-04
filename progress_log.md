# Progress log

Dated record of what was done each session. Newest entry last. Every claim here comes from a command that was actually run. Read this and `decisions_log.md` at the start of every session.

---

## 2026-11-03 (pitch day, late evening) — Phase 1, sub-stages 1A–1D

**Done**
- **1A, folders:** created `connectome/` (with `data/raw/`), `fly/`, `sim/`, `models/`, `eval/`, `demo/`, `configs/`, `tests/`, `notebooks/` (with `figures/`), `logs/`. Each has a short README.
- **1B, environment:** `pyproject.toml`, `uv.lock`, `.venv/` created. CPU-only PyTorch, chosen by Pavan.
- **1C, simulator smoke test:** gym-pybullet-drones installed from GitHub, pinned to commit `15c426c`. `sim/env_check.py` ran one headless step and rendered one 128×128 camera frame. Output in `logs/env_check.txt` (PASS).
- **1D, tests and lint:** `tests/test_environment.py` (3 tests, all pass). `ruff check` and `ruff format --check` clean.

**Installed versions** (from the lock file): Python 3.12.16, numpy 2.5.4, pybullet 3.2.7, torch 2.15.0 (CPU), gymnasium 1.4.0, gym-pybullet-drones 2.2.0, pytest 9.2.0, ruff 0.17.3.

**Problems found**
- Python 3.11 was pinned first. gym-pybullet-drones now requires Python 3.12 or newer, so the project moved to 3.12 and the environment was rebuilt (see `decisions_log.md`).

**Not done**
- Nothing committed to Git. No FlyWire access check yet. No science code yet.

## 2026-11-04 — Phase 1, sub-stage 1E

**Done**
- **1E, config and logs:** created `configs/prereg.yaml` (draft), `progress_log.md`, `decisions_log.md`.

**Next**
- Phase 1 review by Pavan, then Phase 2 (FlyWire data pull). First task: verify the access route (2.1).
