# Decisions log

Dated record of every decision and every deviation from the plan. Newest entry last. The original design decisions (27 of them) are in `02_locked_decisions.md`; they are not repeated here. This file records decisions made while building, and any change to a locked value.

Format: date · decision · reason · who decided.

---

## 2026-11-03

1. **Git repository exists.** Created by Pavan before Phase 1 began; one commit ("Add implementation"). This settles the Phase 1.2 question.
   *Decided by:* Pavan.

2. **Open question: `.gitignore`.** It currently excludes nine files, including the planning documents, the abstract and the deck. Only `02_locked_decisions.md` is tracked. Not changed. Waiting for Pavan to say whether this is intended.
   *Status:* open.

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

## Still open from earlier planning (see `06_open_items.md`)

- How to handle the differences between the abstract and the locked plan (motion front end, dodge direction, sweep sizes).
- Teammate roles on the slides (placeholders for now).
- Exact seed counts and the angle thresholds (set in Phase 8).
