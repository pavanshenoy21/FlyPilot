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
    *Status:* open. Touches locked decisions 3 and 5, so it needs Pavan's approval.

15. **Open: keep weak connections?** Our table includes connections of 1–4 synapses; FlyWire's Codex tables drop connections under 5 synapses. Dropping them would remove 48% of the left giant fiber's source neurons and 23% of the right's. Recommended: keep everything (weights are proportional to synapse count, so weak connections contribute little anyway), and run the 5-synapse version later as a sensitivity check.
    *Status:* open. Decide at Gate G1.

16. **Planning documents moved to `docs/`.** Done by Pavan, who also updated `.gitignore`. Claude then made path fixes only: removed the stale root entry `02_locked_decisions.md` and trailing spaces from `.gitignore` (same ignore behaviour), and updated `CLAUDE.md`, `docs/03`, `docs/07`, `docs/08` and `configs/prereg.yaml` to the new paths. Documents 01-07 stay out of Git; this closes entry 2.
    *Decided by:* Pavan (layout and ignore list); path fixes by Claude.

17. **Commit workflow.** Pavan makes every commit. After each finished sub-stage Claude gives a ready-to-paste commit message and lists the files it covers. Recorded in `CLAUDE.md` and `docs/07`.
    *Decided by:* Pavan.

18. **Open: a compiled `.pyc` file is tracked in Git** (`tests/__pycache__/test_environment.cpython-312-pytest-9.2.0.pyc`). It was committed before `__pycache__/` was ignored. Fix: `git rm --cached -r tests/__pycache__`, then commit.
    *Status:* waiting for Pavan.

19. **Receptive-field method (proposed, confirm at Gate G1):** take each neuron's receptive-field position from the centre of its input synapses in the lobula (and lobula plate), estimated from a random sample of batches of the FlyWire synapse table (details in `progress_log.md`, 3B). The annotation file's position columns are not used.
    *Why:* real connectome data, same data source as the wiring, and the probe shows it is stable and spread over the lobula.
    *Open:* the angular calibration (lobula position to visual-field angle) and a larger sample (about 15%) are still to do in Phase 5.4; fallback is even tiling with published receptive-field sizes.
    *Status:* proposed by Claude, pending Pavan at Gate G1.

## Still open from earlier planning (see `06_open_items.md`)

- How to handle the differences between the abstract and the locked plan (motion front end, dodge direction, sweep sizes).
- Teammate roles on the slides (placeholders for now).
- Exact seed counts and the angle thresholds (set in Phase 8).
