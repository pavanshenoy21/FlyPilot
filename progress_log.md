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

## 2026-11-07 — Phase 3, sub-stage 3A (connection strength)

**Done**
- `connectome/analyze_subgraph.py` with tests (`tests/test_analyze_subgraph.py`). Whole suite: 27 passed, ruff clean. Writes `connectome/data/subgraph_v783/analysis.json` and `notebooks/figures/subgraph_weights.png`.

**Synapses per source neuron** (one connection = one neuron pair):

| Giant fiber | Source | Neurons | Synapses | Mean | Median | Range | Top 10% of neurons hold |
|---|---|---|---|---|---|---|---|
| left | LC4 | 54 | 374 | 6.9 | 7 | 1–14 | 21% |
| left | LPLC2 | 94 | 458 | 4.9 | 4 | 1–15 | 27% |
| right | LC4 | 50 | 431 | 8.6 | 8 | 3–16 | 17% |
| right | LPLC2 | 95 | 622 | 6.6 | 7 | 1–16 | 22% |

The input is spread across many neurons; no small group dominates (the strongest 10% of neurons hold only 17–27% of the synapses). This suits a population circuit.

**Finding 1 — a left/right asymmetry.** The right giant fiber receives 1,053 synapses from our sources, the left only 832 (27% more on the right). Connections are also stronger on the right (mean 6.6 and 8.6 synapses against 4.9 and 6.9). With one global scale, a perfectly symmetric looming stimulus would drive the right giant fiber harder, so it would tend to fire first. Our dodge-direction rule (decision 5: the first giant fiber to fire gives the threat side) would then be biased towards one side. The shuffle control keeps degrees, so it keeps this asymmetry too. **Needs a decision before Phase 6 (open item, see decisions_log 14).**

**Finding 2 — weak connections.** FlyWire's own Codex tables leave out weak connections; ours (the Zenodo table) includes everything. If connections under 5 synapses were dropped, the left giant fiber would keep only 77 of 148 source neurons (52%, and 76% of synapses); the right would keep 111 of 145 (77%, and 92% of synapses). That would also deepen the left/right asymmetry. **Needs a decision (open item, see decisions_log 15).**

**Next**
- 3B: can each neuron's receptive field (where in the visual field it looks) be recovered from the data?
- 3C: Gate G1 write-up and decision.

## 2026-11-07 — housekeeping after the move to `docs/`

**Done**
- Checked the new layout. Pavan moved documents 01-09 into `docs/` and committed Phase 3A; the planning documents 01-07, `CLAUDE.md`, the abstract and the original deck are kept out of Git on purpose.
- Fixed paths and stale text: `.gitignore` (stale root entry and trailing spaces), `CLAUDE.md` (rewritten: new paths, commit-message rule, current state), `docs/03`, `docs/07`, `docs/08`, `configs/prereg.yaml`, both logs.
- Found a compiled `.pyc` file tracked in Git (decisions_log 18); Pavan to remove it from tracking.

**Next**
- 3B: can each neuron's receptive field be recovered from the data? (done below)

## 2026-11-07 — Phase 3, sub-stage 3B (receptive fields)

**Question:** can each LPLC2 / LC4 neuron's receptive-field position (where in the visual field it looks) be recovered from the data? Their dendrites sit in the lobula (LO) and lobula plate (LOP), which are retinotopic layers, so the centre of a neuron's input synapses there is a proxy for where it looks.

**Answer: yes, from synapse positions. Not from the annotation file.**
- **Annotation positions are no use.** In `nodes.csv`, `pos` and `soma` points fall in a tight cluster (about 25 x 13 x 6 micrometres, with the usual 4 x 4 x 40 nm voxel assumption): the cell-body patch, not the dendrites. I first got a misleading "flat sheet" result by running the principal-component test in raw voxel units; redoing it in physical units removed it.
- **The input synapses are in the right place.** From the connection table, each source neuron has a median of 1,003 input synapses (lower bound), about 90% of them in LO/LOP.
- **The synapse table has what is needed** (`flywire_synapses_783.feather`, 9.49 GB, 1,985 batches of 65,536 rows, with a 3D position and a neuropil for every postsynaptic site), but it is **shuffled**: every sampled batch has the same neuropil mix and a wide spread of neuron ids. A single neuron's rows cannot be fetched, but any random subset of batches is an unbiased sample for every neuron.
- **Method** (`connectome/probe_receptive_fields.py`, tested): read a random subset of batches with HTTP range requests, keep rows of our 293 source neurons in LO/LOP, take per-neuron centroids.
- **Probe result** (random 40 of 1,985 batches, about 2%, 192 MB, 98 s): every one of the 293 neurons has lobula sites (median 10, 5th percentile 3). Two independent halves of the sample agree on a neuron's centre to a median of 5.2 um, while neuron centres differ by 20-38 um across the lobula (std in x and y), so the differences are 4-7 times the sampling error even at 2%. The plot (`notebooks/figures/receptive_field_probe.png`) shows each lobula filled by a patch of about 100 x 140 um, with the right lobula a mirror image of the left.

**Mistake caught:** my first run assumed the synapse table is in 4 x 4 x 40 nm voxels, which gave impossible z spreads (570-760 um). Checked against the annotation positions: the table is in nanometres on all axes (about 4x in x, about 40-60x in z). Corrected in the code and tests; the earlier numbers are discarded.

**Still to do (not a blocker for G1):**
1. **Bigger sample.** At 2% only 129 of 293 neurons have at least 5 sites in each half. A 15% sample (about 300 batches, 1.5 GB, roughly 12 minutes at the 2 MB/s seen with 4 parallel readers) should give about 75 sites per neuron. Planned for Phase 5.4.
2. **Angular calibration.** Centroids give each neuron's position in the lobula, not a visual-field angle. Turning one into the other needs the orientation of the retinotopic axes (which direction in the lobula is "up" or "forward"). Fallback if that proves too hard: tile the neurons evenly over the visual field, using published receptive-field sizes (needs citations).

**Tests:** 6 new tests for the pure functions (the network reader is not unit-tested, since it needs the 9.5 GB remote file). Whole suite: 33 passed. `ruff check` and `ruff format --check` clean.

**Next**
- 3C: Gate G1 write-up and decision.

## 2026-11-07 — Phase 3, sub-stage 3C (Gate G1 report)

**Done**
- `connectome/asymmetry_check.py` (run as `.venv/bin/python -m connectome.asymmetry_check`) with 3 tests; writes `connectome/data/subgraph_v783/asymmetry.json`. Whole suite: 36 passed; ruff clean.
- `docs/10_gate_g1_report.md`: the Gate G1 write-up (criteria against evidence, findings, decisions, draft limitations).
- `configs/prereg.yaml`: proposed rule for the left/right asymmetry added (marked proposed).

**New evidence on the left/right asymmetry** (decisions_log 14):
- The right giant fiber gets more input from every kind of neuron: LC4 1.15x, LPLC2 1.36x, all other neurons 1.17x (right over left). So it is partly a property of the giant fiber, not only of LPLC2 / LC4.
- Left source neurons have fewer total input synapses (median LC4 1,207 against 1,382; LPLC2 765 against 996), which could be tracing completeness or biology; the data cannot tell which.
- The LPLC2 to giant-fiber gap (about 26%) is larger than LPLC2's overall output gap (about 8%).

**Gate G1 verdict (recommended): PASS**, pending Pavan's answers to decisions 13, 14, 15 and 19 (and housekeeping item 18). Not yet tested: whether the circuit fires the giant fiber selectively for looming (Gate G2, Phase 6).

**Next**
- Phase 4 (LIF core), after Pavan confirms G1.

## 2026-11-07 — Gate G1 closed; Phase 4, sub-stage 4A (LIF neuron and synapse)

**Gate G1:** Pavan said "proceed", taken as approval of the report's recommendations: verdict PASS, decisions 13, 14, 15 and 19 as recommended (`decisions_log.md` updated). Still for Pavan: `git rm --cached -r tests/__pycache__` (18).

**Done (4.1, 4.2, 4.5)**
- `configs/lif_params.yaml`: fixed constants with sources. Values taken from Shiu et al. 2024 and checked against the authors' code (`philshiu/Drosophila_brain_model`, `model.py`): rest/reset -52 mV, threshold -45 mV, membrane tau 20 ms, synaptic tau 5 ms, refractory 2.2 ms, delay 1.8 ms, 0.275 mV per synapse. The last is a placeholder for our one global scale (tuned in Phase 6). Nothing tuned.
- `fly/lif.py`: `LIFParams`/`load_params`, `transmitter_sign`, `synaptic_matrix` (weight = sign x synapse count x scale), `LIFNetwork.step` (Euler, dt 0.1 ms, refractory period, synaptic delay as a ring buffer). Generic: no fly code in it.
- `tests/test_lif.py` (9 tests): constants match the source; constant drive of 10 mV fires at the analytic rate within 5%; drive below threshold never fires; no inter-spike gap under 2.2 ms; sign follows the transmitter (unknown transmitter raises); weight doubles with count; excitatory input depolarises and inhibitory input hyperpolarises the target; input arrives exactly 18 steps (1.8 ms) after the spike; reset restores the state.
- `configs/prereg.yaml`: `lif_constants` and `receptive_fields` filled in; asymmetry rule marked approved.

**Checks:** whole suite 45 passed; `ruff check` and `ruff format` clean.

**Limits to remember:** `i_ext` (direct input in mV) is our addition for tests and the stimulus drive. The synaptic current is a single exponential decay, as in the source code, not a true alpha function.

**Next:** 4B: spike recording (4.3) and the network runner with an input schedule (4.4), tested on a toy 3-neuron graph.

## 2026-11-07 — Phase 4, sub-stage 4B (spike recording and network runner)

**Done (4.3, 4.4)**
- `fly/lif.py`: `SpikeRecord` (every spike as step and neuron index; times in ms, per-neuron counts, first-spike time, save and load as `.npz`), `run_network(net, n_steps, schedule, watch)` (resets, runs, returns the record and optional voltage traces; the schedule is an array `[steps, neurons]`, a function of the step, or none) and `run_graph(node_ids, edges, scale, n_steps, schedule)` (builds the weight matrix and runs).
- `tests/test_lif.py`: now 14 tests. New: toy 3-neuron graph (driven neuron fires, its target fires after it, the inhibited neuron never fires and drops below rest); no input gives no spikes; schedule as array equals schedule as function; two runs of the same network give identical spikes; spike record round-trips through a file.
- `fly/demo_lif.py` (added after 4A): a runnable look at the 3-neuron chain.

**Checks:** whole suite 50 passed; ruff clean.

**Phase 4 acceptance:** all tests pass; no parameter tuned against looming data. Met. The runner handles the 295-node subgraph only as a dense matrix (295 x 295), which is fine at this size.

**Next:** Phase 5, stimuli and the Reichardt front end. 5.1 first: synthetic looming, passing and receding dots with exact time-to-collision.

## 2026-11-07 — Phase 5, sub-stage 5.1 (synthetic stimuli)

**Done**
- `sim/stimuli.py`: analytic dark-sphere stimuli seen by a pinhole camera with the simulator's settings (60 degree field of view, 128 x 128, 30 fps). `make_looming`, `make_passing`, `make_receding`, and `make_stimulus(kind, seed)` (random draw from the documented `RANGES`, same seed gives the same stimulus). Each `Stimulus` carries frames, times, exact TTC per frame (nan unless looming), disc radius and centre in pixels. Impact is defined as the sphere's nearest surface reaching the camera plane, so TTC = (z - radius) / speed. The outline is drawn as a disc of radius f R / sqrt(z^2 - R^2), anti-aliased (exact on the optical axis, a small approximation off-axis).
- `tests/test_stimuli.py` (12 tests): TTC counts down exactly one frame at a time and ends within one frame of impact; apparent size follows the geometry; the classic estimate radius / (d radius / dt) agrees with the true TTC to 8% early in a loom; rendered area matches the disc to 3%; passing keeps constant size, has no TTC and crosses the view; receding shrinks; seeds are reproducible; ranges respected; unknown kind rejected.
- `notebooks/figures/synthetic_stimuli.png`: contact sheet of the three kinds (checked by eye).

**Checks:** whole suite 62 passed; ruff clean.

**Not yet decided:** how fast the real episodes' objects move relative to these ranges (the ranges are placeholders for the front-end work, not the evaluation set; the evaluation episodes come from the simulator generator in a later phase). Dark object on a bright background only; polarity variants are a robustness question for later.

**Next:** 5.2 coarse grid downsampler, then 5.3 Reichardt motion detector.

## 2026-11-07 — Phase 5, sub-stage 5.2 (coarse grid downsampler)

**Done**
- `fly/frontend.py`: `coarse_grid(frames, n=12)` area-averages [..., 128, 128] frames to [..., 12, 12] with an exact weighted averaging matrix (partial pixels weighted by overlap, so 128 to 12 works although 128 is not divisible by 12). Fixed linear map, no parameters.
- Grid choice: 12 x 12 cells of 5 degrees over the 60 degree field of view, about a fly's inter-ommatidial angle (4.5-5 degrees). **The 5 degree figure is from memory; a citation must be added before the report.** Written into `configs/prereg.yaml` as `fly.coarse_grid`.
- `tests/test_frontend.py` (8 tests): shapes for a frame and a stack; matrix rows sum to 1; mean intensity preserved; constant image stays constant; equals a plain block average when sizes divide (128 to 16); a dark corner lands in the right cell; a growing looming dot darkens more of the grid; linear (no learned parameters).

**Checks:** whole suite 70 passed; ruff clean.

**Declared simplification:** the pinhole image is not equal-angle per pixel (about 25% stretch at 30 degrees from the centre); the 12 x 12 cells are treated as equal.

**Next:** 5.3 Reichardt-style ON/OFF motion detector on the grid, tested on a bar moving in known directions.

## 2026-11-07 — Phase 5, sub-stage 5.3 (Reichardt motion detector)

**Done**
- `fly/frontend.py`: `on_off` (frame-to-frame change split into ON = brightening and OFF = darkening, like T4 / T5), `low_pass` (first-order delay filter), `reichardt(grid)` -> `[T, 2 polarities, 4 directions (right, left, down, up), 12, 12]`. Correlator per neighbouring cell pair: delayed(a) x b - a x delayed(b), separately in ON and OFF; positive and negative halves give the two opposite directions. No learned parameters.
- One chosen constant: delay filter tau = 50 ms (about 1.5 frames at 30 fps). **Chosen, not fitted and not cited**; recorded as such in the code.
- `sim/stimuli.py`: `moving_bar(direction, speed, width, dark)` test pattern.
- `tests/test_frontend.py`: now 22 tests. New: a dark and a bright bar moving in each of the 4 directions gives its largest energy in the correct direction in both ON and OFF (16 cases); static image gives exactly zero; full-field flicker gives zero; ON/OFF split; low-pass step response; a centred looming dot gives outward motion in all four halves; **control:** the same bar with its frames shuffled in time gives no clear direction (right/left ratio 1.11 ON, 0.94 OFF).

**Measured (not just asserted):** bars give energy only in their true direction (opposite direction exactly 0 for a single bar). Looming dot: rightward >> leftward on the right half and the reverse on the left half.

**Checks:** whole suite 84 passed; ruff clean.

**Limits:** ON/OFF uses a plain frame difference (no adaptation); the detector only compares nearest neighbours (5 degrees apart), so very fast motion (more than one cell per frame, about 150 degrees/s) may alias. Feeding LC4 the same motion signal as LPLC2 is a declared simplification (locked decision 11).

**Next:** 5.4 receptive-field mapping per LPLC2 / LC4 neuron (larger synapse sample and the angular calibration), then 5.5 front-end response plots.
