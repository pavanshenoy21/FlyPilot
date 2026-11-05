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

## 2026-11-05 — Phase 2, sub-stage 2B (download and verify)

**Done**
- `.gitignore` now ignores `connectome/data/raw/` and `__pycache__/` (checked with `git check-ignore`). `pandas` 3.1.0 and `pyarrow` 26.0.1 added to the project.
- Downloaded into `connectome/data/raw/`: `proofread_connections_783.feather` (852,022,274 bytes), `proofread_root_ids_783.npy`, `Supplemental_file1_neuron_annotations.tsv`. Both Zenodo files match their published MD5 checksums. The annotation file's SHA-256 starts `b214970b55d2fbe0` (no published checksum to compare).
- The big download was interrupted once (curl error 56, connection timed out) at 87%. I resumed it with `curl -C -` and re-verified; my first "done" marker had been written even though curl failed, so I checked the file size and checksum and did not trust the marker.

**Answers to the three open points** (release 783, numbers from inline analysis, not yet a saved script):

1. **Transmitter data is in the connection table.** Columns: `pre_pt_root_id`, `post_pt_root_id`, `neuropil`, `syn_count`, and per-connection average transmitter probabilities `gaba_avg`, `ach_avg`, `glut_avg`, `oct_avg`, `ser_avg`, `da_avg`. 16,847,997 rows (one per neuron pair per neuropil); 15,091,983 distinct neuron pairs; 54,492,922 synapses in total.
2. **Root ids line up.** 139,241 of 139,248 annotated neurons (99.99%) are in the 783 proofread list. 14 proofread ids have no annotation row.
3. **Connections into the giant fibers.** The giant fiber is cell type `DNp01` (hemibrain label "Giant Fiber").

| | Right GF | Left GF |
|---|---|---|
| Presynaptic neurons / synapses (all inputs) | 483 / 5,147 | 479 / 4,327 |
| LPLC2 → GF | 95 neurons, 622 synapses | 94 neurons, 458 synapses |
| LC4 → GF | 50 neurons, 431 synapses | 54 neurons, 374 synapses |
| LPLC2 + LC4 share of GF input synapses | 20.5% | 19.2% |
| Side of LPLC2/LC4 inputs | 100% right | 100% left |

**What this means for Gate G1**
- **Same-side input holds completely.** Every LPLC2 and LC4 neuron feeding a giant fiber sits on that fiber's own side. This supports the two-giant-fiber direction rule (decision 5).
- **The circuit is a partial model of the giant fiber.** LPLC2 and LC4 supply only about 20% of each giant fiber's input synapses. The other top inputs are other cell types (CB3707, DNp70, PVLP122b, SAD014, CL038, PVLP010, ...), which our circuit leaves out. Must be declared as a limitation.
- **Low transmitter confidence on the giant fibers:** `top_nt_conf` is 0.27 (right) and 0.32 (left), which is why their predicted transmitters disagree. Irrelevant for our readout, as noted earlier.
- **About 6–8% of LPLC2 neurons** (7 of 102 right, 14 of 108 left) do not connect to a giant fiber directly. Not an error, but the subgraph builder must handle neurons with no path.

## 2026-11-05 — Phase 2, sub-stage 2C (build the subgraph)

**Done**
- `connectome/build_subgraph.py`: small testable functions; selects LPLC2 and LC4 neurons and the two giant fibers (DNp01), collapses per-neuropil rows into one edge per neuron pair, assigns signs, writes `nodes.csv`, `edges.csv`, `summary.json` to `connectome/data/subgraph_v783/` (tracked in Git, about 100 KB).
- `tests/test_subgraph.py`: 14 tests, 13 on small synthetic tables plus one that reruns the real data and checks the 2B numbers. Whole suite: 22 passed. `ruff check` and `ruff format` clean.
- `configs/data_version.yaml`: pins the release, file sizes, MD5 and SHA-256 checksums, and the output hashes.

**The subgraph** (direct LPLC2 / LC4 → giant fiber only, as agreed): 295 nodes (2 giant fibers + 293 source neurons), 293 edges, 1,885 synapses. Right giant fiber: 145 sources, 1,053 synapses. Left giant fiber: 148 sources, 832 synapses. 100% of synapses are same-side. The 21 LPLC2 neurons with no direct edge (14 left, 7 right) are left out of the nodes; every LC4 neuron has an edge. The numbers match the 2B check exactly.

**Finding: the per-connection transmitter data disagrees with the neuron-level label.** The connection table gives, per connection, an average predicted probability for each transmitter. For our 293 edges:
- The most probable transmitter is glutamate for 144 edges (1,028 synapses, 55%), acetylcholine for 108 edges (633 synapses), dopamine for 37, GABA and serotonin for 2 each. It agrees with the neuron-level label on only 33.6% of synapses.
- It is not small-sample noise: agreement does not improve on larger edges (42% on edges of 1–2 synapses, 30% on edges of more than 10).
- The neuron-level label says acetylcholine for all 314 LPLC2 and LC4 neurons, and the annotation file's `known_nt` column backs this with experimental evidence for every one of them (source: Davis et al. 2020, TAPIN-seq).
- Per-connection probabilities are diffuse (synapse-weighted means: ach 0.30, glut 0.34, dopamine 0.20), so the top pick is often a near-tie.

**Resolution (decision 13):** signs use `known_nt` when it exists, otherwise `top_nt`. All 293 edges used `known_nt`, so all 293 are excitatory and no synapses are dropped. The per-connection numbers stay in `edges.csv` for comparison only. To be stated as a limitation: the transmitter evidence is neuron-level, and the per-connection predictions disagree with it.

**Not verified:** whether the experimental evidence (TAPIN-seq) reflects the transmitter used at the giant-fiber synapses specifically. I'm trusting the annotation file's `known_nt` and its stated source; I have not read the Davis et al. paper.

**Next**
- Phase 2 is complete when you've reviewed 2A–2C. Then Phase 3 (subgraph analysis and Gate G1): the remaining analysis is receptive-field extraction, a subgraph figure, and the G1 write-up.
