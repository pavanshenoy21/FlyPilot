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

## 2026-11-04 — Phase 2, sub-stage 2A (FlyWire access route)

**Checked from this machine** (all returned HTTP 200): codex.flywire.ai, flywire.ai, zenodo.org.

**Route 1 — bulk connectivity, no account needed.** Zenodo record 10676866, snapshot **783**, published 2024-06-02, license CC-BY 4.0. Files: `proofread_connections_783.feather` (852 MB), `proofread_root_ids_783.npy` (1.1 MB), `per_neuron_neuropil_count_pre/post_783.feather` (17 MB / 234 MB), `flywire_synapses_783.feather` (9.5 GB, not needed).

**Route 2 — cell types, side and predicted transmitter, no account needed.** GitHub `flyconnectome/flywire_annotations`, file `supplemental_files/Supplemental_file1_neuron_annotations.tsv` (31.7 MB, downloaded and read to scratch space). 139,248 rows, 31 columns, including `root_id`, `cell_type`, `hemibrain_type`, `side`, `top_nt`, `top_nt_conf`, `known_nt`. The repo's LICENSE file returned 404, so the annotation licence is **unconfirmed**; cite Schlegel et al. 2024 and Matsliah et al. 2024.

**Route 3 — live CAVE / fafbseg.** Needs a FlyWire account and an API token. Not needed for our plan.

**Neuron counts found in the annotation file** (release 783):

| Cell type | Left | Right | Total | Predicted transmitter |
|---|---|---|---|---|
| LPLC2 | 108 | 102 | 210 | acetylcholine (excitatory) |
| LC4 | 54 | 50 | 104 | acetylcholine (excitatory) |
| Giant Fiber | 1 | 1 | 2 | left: acetylcholine; **right: glutamate** |

**Flag:** the right giant fiber's predicted transmitter is glutamate, the left's is acetylcholine. The giant fiber is a cholinergic neuron, so the right-hand label looks like a prediction error. It does not affect our design, because the sign of a connection comes from the neuron that sends it (LPLC2/LC4, both acetylcholine) and we only read the giant fiber's spikes. It would matter only for connections going out of the giant fiber, which we do not use. Record it in the report as a limitation.

**Not yet verified**
- Column names of `proofread_connections_783.feather` (is a transmitter column present?).
- Whether the annotation file's `root_id` values match the 783 root-id list.
- How many connections run from LPLC2/LC4 to each giant fiber.

**Next**
- 2B: download the two files into `connectome/data/raw/` (after `.gitignore` covers it), then check the three points above.
