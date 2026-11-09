# Decisions log

Dated record of every decision and every deviation from the plan. Newest entry last. The original design decisions (27 of them) are in `02_locked_decisions.md`; they are not repeated here. This file records decisions made while building, and any change to a locked value.

Format: date · decision · reason · who decided.

---

## 2026-11-03

1. **Git repository exists.** Created by Pavan before Phase 1 began; one commit ("Add implementation"). This settles the Phase 1.2 question.
   *Decided by:* Pavan.

2. **`.gitignore` question: resolved.** Pavan keeps the planning documents out of Git on purpose and updated the list himself after moving them to `docs/` (see entry 16).
   *Status:* resolved 2026-11-07.

3. **Folder layout accepted** as in `03_implementation_plan.md`, plus `logs/`. Each folder got a short README.
   *Decided by:* Pavan (confirmed at the end of 1A).

4. **PyTorch is CPU-only on the local machine.** CNN training runs on Colab's A100.
   *Reason:* small install (about 200 MB, not several GB); the local GPU isn't needed for the plan.
   *Decided by:* Pavan.

5. **Python 3.12, not 3.11 (correction).** I first pinned 3.11 on an assumption. gym-pybullet-drones' current `pyproject.toml` requires `python = "^3.12"`, so the project and its environment moved to 3.12.
   *Deviation from:* my own first 1B setup, not from a locked decision.
   *Decided by:* Claude, reported to Pavan.

6. **gym-pybullet-drones pinned to commit `15c426c85ac8e7a5db66d8b100f48858133357f6`**, installed as a git dependency through `uv`. It isn't on PyPI. It brings in stable-baselines3, which we don't use.
   *Decided by:* Claude, approved by Pavan (asked in 1B).

7. **Three environment sanity tests added in 1D**, although the plan said zero tests. Plain `pytest` exits with an error when it finds no tests. The tests check the Python version, the imports, and one headless simulator step. They contain no science.
   *Deviation from:* `07_phased_implementation_plan.md` task 1.5.
   *Decided by:* Claude, reported to Pavan.

8. **Camera findings from the 1C smoke test** (facts, not yet decisions): the library camera has a fixed 60° field of view and aspect 1.0, so frames must be square. A 128×128 frame renders fine. Default capture rate is 24 fps, but 30 fps is reachable by capturing every 8th step at 240 Hz. Frames arrive as 64-bit integers and must be cast.
   *Open:* the final frame size is `tbd` in `prereg.yaml`. 128×128 is proposed. To be confirmed before G4.

## 2026-11-04

9. **`configs/prereg.yaml` created as a draft.** Values already locked in `02` and `04` are filled in with their decision numbers. Everything not yet decided is `tbd`, never guessed. It is frozen at Gate G4 (Phase 8).
   *Decided by:* Claude, to be reviewed by Pavan.

## 2026-11-05

10. **FlyWire data route: Zenodo snapshot 783 plus the public annotation file.** No FlyWire account or token is needed. Files saved in `connectome/data/raw/`, checksums verified.
    *Decided by:* Claude, approved by Pavan (2B go-ahead).

11. **`.gitignore` extended** with `connectome/data/raw/` and `__pycache__/`. The existing nine-file list was left alone (that question is still open, see below).
    *Decided by:* Claude, approved by Pavan.

12. **`pandas` and `pyarrow` added to the project** (needed to read the Feather files).
    *Decided by:* Claude, reported to Pavan.

13. **Transmitter signs come from the neuron-level label, not the per-connection probabilities.** Rule: use `known_nt` (experimental, Davis et al. 2020 for all LPLC2 and LC4) when the annotation file has it, otherwise `top_nt` (FlyWire's prediction). The locked rule (decision 3 in `02`) is unchanged: ACh excitatory, GABA and glutamate inhibitory. Result: all 293 edges excitatory, none dropped.
    *Reason:* the per-connection probabilities pick glutamate for 55% of our synapses and agree with the neuron-level label on only 33.6% of them, and the disagreement does not shrink on bigger edges. The experimentally known label is the stronger evidence. See `progress_log.md`, 2C.
    *Decided by:* Claude, **pending Pavan's review**. It affects every connection weight sign, so it is worth a second look.
    *To report:* as a limitation.

## 2026-11-07

14. **Open: how to handle the left/right asymmetry.** The right giant fiber gets 27% more synapses from our sources than the left (1,053 against 832). A single global scale would bias the "first giant fiber to fire" direction rule towards the right. Options: (a) accept it and measure the bias in Phase 6, (b) one scale per side, tuned so that a symmetric stimulus gives equal responses (adds one tuned number), (c) normalise each giant fiber's total input weight. Recommended: (a) first, then (b) only if the bias is large. Decide at Gate G1.
    *New evidence (3C):* the right giant fiber gets more input from every kind of neuron (LC4 1.15x, LPLC2 1.36x, others 1.17x), so it is partly a giant-fiber property. Proposed rule written into `configs/prereg.yaml`: accept, measure on symmetric stimuli in Phase 6, and switch to one scale per giant fiber only if the right fires first on more than 60% or fewer than 40% of symmetric trials.
    *Status:* **approved by Pavan ("proceed", 2026-11-07) as recommended** (accept, measure in Phase 6, switch rule in prereg.yaml).

15. **Open: keep weak connections?** Our table includes connections of 1–4 synapses; FlyWire's Codex tables drop connections under 5 synapses. Dropping them would remove 48% of the left giant fiber's source neurons and 23% of the right's. Recommended: keep everything (weights are proportional to synapse count, so weak connections contribute little anyway), and run the 5-synapse version later as a sensitivity check.
    *Status:* **approved as recommended** (keep everything; 5-synapse sensitivity run later).

16. **Planning documents moved to `docs/`.** Done by Pavan, who also updated `.gitignore`. Claude then made path fixes only: removed the stale root entry `02_locked_decisions.md` and trailing spaces from `.gitignore` (same ignore behaviour), and updated `CLAUDE.md`, `docs/03`, `docs/07`, `docs/08` and `configs/prereg.yaml` to the new paths. Documents 01-07 stay out of Git; this closes entry 2.
    *Decided by:* Pavan (layout and ignore list); path fixes by Claude.

17. **Commit workflow.** Pavan makes every commit. After each finished sub-stage Claude gives a ready-to-paste commit message and lists the files it covers. Recorded in `CLAUDE.md` and `docs/07`.
    *Decided by:* Pavan.

18. **Open: a compiled `.pyc` file is tracked in Git** (`tests/__pycache__/test_environment.cpython-312-pytest-9.2.0.pyc`). It was committed before `__pycache__/` was ignored. Fix: `git rm --cached -r tests/__pycache__`, then commit.
    *Status:* still to run by Pavan: `git rm --cached -r tests/__pycache__`.

19. **Receptive-field method (proposed, confirm at Gate G1):** take each neuron's receptive-field position from the centre of its input synapses in the lobula (and lobula plate), estimated from a random sample of batches of the FlyWire synapse table (details in `progress_log.md`, 3B). The annotation file's position columns are not used.
    *Why:* real connectome data, same data source as the wiring, and the probe shows it is stable and spread over the lobula.
    *Open:* the angular calibration (lobula position to visual-field angle) and a larger sample (about 15%) are still to do in Phase 5.4; fallback is even tiling with published receptive-field sizes.
    *Status:* **confirmed** ("proceed", 2026-11-07).

20. **Gate G1 report written** (`docs/10_gate_g1_report.md`). Recommended verdict: PASS, with decisions 13, 14, 15 and 19 to confirm. Gate G1 is not closed until Pavan answers.
    *Status:* **Gate G1 closed: PASS** on Pavan's "proceed" (2026-11-07), taken as approval of 13, 14, 15 and 19 as recommended.

21. **LIF constants come from Shiu et al. 2024 (whole-brain fly LIF model), checked against the authors' code** (`philshiu/Drosophila_brain_model`, `model.py`): rest and reset -52 mV, threshold -45 mV, membrane tau 20 ms, synaptic tau 5 ms, refractory 2.2 ms, delay 1.8 ms, weight 0.275 mV per synapse (their only free parameter). Used as fixed published values, not tuned. The weight per synapse is the placeholder for our one global scale, which Phase 6 tunes.
    *Decided by:* Claude, from published values; Pavan can veto.

22. **Receptive-field map (Phase 5.4).** Each eye's lobula centroids (15% synapse sample) are projected onto their sheet and scaled to fill its half of the 12 x 12 grid (left eye -> left half, right eye -> right half). Vertical: dorsal lobula = up, checked from the data (FlyWire y grows ventrally). Horizontal: anterior lobula = frontal (image centre), posterior = outer edge. **This horizontal orientation is an assumption** (the two optic chiasms each invert the front-back axis; the final direction in FlyWire coordinates is not verified). The flipped map is pre-registered as a sensitivity check, reported alongside, never swapped in after results. Declared simplification: each eye's ~160 degree map is squeezed into a 30 x 60 degree half-image. Receptive-field size is left to Phase 6.
    *Decided by:* Claude (method within decision 19); Pavan can veto.

23. **Synthetic looming stimuli are on a true collision course.** In 5.5 some random looming stimuli had a sideways offset larger than the sphere's radius (near misses, not collisions). Fix: the offset is drawn inside a disc of 0.8 x the radius. Synthetic stimuli are front-end test material only; the evaluation episodes come from the simulator generator.
    *Decided by:* Claude (bug fix).

24. **Circuit assembly choices (Phase 6.1), fixed, not fitted:** receptive field = grid cells within 2 cells (10 degrees) of the neuron's centre, about a third of the grid height (published LPLC2 receptive fields are about 60 degrees of a ~160 degree eye; value from memory, citation to check: Klapoetke et al. 2017). LPLC2 drive = mean over its receptive field of outward minus inward motion relative to its centre, rectified. LC4 drive = mean outward motion only. Frames held for one frame period (33.3 ms) as input to the LIF network.
    *Decided by:* Claude; Pavan can veto.

25. **The one tuned number is the input gain, not the synapse scale (amends locked decision 3).** Evidence (4 stimuli per kind, seeds 100-103): with the input gain fixed by a reference-edge rule and the synapse scale tuned (the locked plan), LPLC2/LC4 fired only ~5 spikes per loom, the giant fiber missed 1 of 4 looms at scales 5 and 20 mV per synapse, and one input spike could trigger it, so the wiring would barely matter. With the synapse weight fixed at the published 0.275 mV (Shiu et al. 2024) and the input gain varied, the giant fiber fired on 4/4 looms and 0/8 passing or receding at gains 3, 10 and 30, driven by hundreds of source spikes, with TTC at trigger 0.09-0.43 s. Still exactly one tuned number. Decided before any calibration or evaluation run. These 12 exploratory stimuli (seeds 100-103) must not be reused for calibration or testing.
    *Decided by:* Pavan ("okay go ahead", 2026-11-07), on Claude's recommendation.

26. **Input gain frozen at 5.6234 (Phase 6.4)** with hashes of the calibration result and the code in `configs/prereg.yaml`. **Re-calibration on simulator episodes:** in Phase 8, the gain is re-tuned once on 30 simulator episodes with the same pre-registered rule; that becomes the evaluation gain. Gate G2 thresholds and head-on scoring written into prereg before the held-out run (pass: hit rate lower 95% bound >= 0.8 and false-alarm rate upper 95% bound <= 0.2; side scored only when |x| >= 0.02 m).
    *Decided by:* Pavan ("yes freeze ... yess", 2026-11-07); G2 thresholds proposed by Claude, written before the run.

27. **Per-side input gain (pre-registered symmetry rule applied).** The symmetry check fired (right giant fiber first on 37.5% of centred looms). Pavan chose to follow the rule (option 1, 2026-11-09) rather than log a deviation. Form, grid, fresh tuning seeds (4000-4039) and rule were written into prereg before the tuning run. Result: a = 1.0266, left gain 5.4778, right gain 5.7729 (geometric mean still the frozen 5.6234). Independent re-check on seeds 3000-3039: right first 21/40 = 52.5% (95% interval 37-67%). Held-out results unchanged (50/50 looms, 0/100 false alarms, median TTC 189 ms, side 45/46). This adds a second tuned number (the split); it is logged and frozen, and the shuffled circuits get the same treatment.
    *Decided by:* Pavan ("1.", 2026-11-09).

28. **Shuffle method as implemented (Phase 7.1).** Locked decision 12, done as a configuration-model rewire: edge targets permuted across edges, each edge keeps its synapse count and transmitter; duplicates and self-edges redrawn. Wiring seeds 0-19 (their own namespace, separate from stimulus seeds). Each source keeps its total output synapses; each giant fiber keeps its number of inputs but not its total input synapses (which follow the sources it receives). Since every real source has exactly one, same-side connection, the shuffle in practice re-assigns which giant fiber each source drives. Noted before any shuffled circuit was run.
    *Decided by:* Claude, implementing locked decision 12; for Pavan's review.

29. **Shuffles get the real circuit's tuning procedure, not its tuned numbers (Phase 7.2).** Each of the 20 shuffled circuits is calibrated exactly as the real one was: input gain by the same rule on the same calibration seeds and grid; symmetry check on seeds 3000-3039; per-side split only if that check fires (same grid, seeds and rule); then the held-out set. Secondary report: every shuffle on the held-out set at the real circuit's frozen gains. Metrics, ranking (ties half) and a one-sided permutation p-value written into `configs/prereg.yaml` (shuffle.synthetic_check) before any shuffled circuit was run, together with the stated expectation (side accuracy should drop, timing may not). Pipeline smoke-tested on wiring seed 99, outside the pre-registered set.
    *Decided by:* Pavan ("Each shuffle gets the same tuning procedure", 2026-11-09), on Claude's recommendation.

## Still open from earlier planning (see `06_open_items.md`)

- How to handle the differences between the abstract and the locked plan (motion front end, dodge direction, sweep sizes).
- Teammate roles on the slides (placeholders for now).
- Exact seed counts and the angle thresholds (set in Phase 8).
