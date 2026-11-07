# 08 — Project guide: every folder, file and component

This is the map of the project. It says what each file is for, what each planned folder will hold, what each scientific and engineering term means here, and how the parts connect. Status is marked for every item: **exists** (on disk now), **planned** (designed, not created) or **placeholder** (exists but is empty or temporary).

Snapshot date: 7 Nov 2026 (after Phase 3A). The numbered documents now live in `docs/`.

---

## 1. What is on disk right now

```
Bio-Insp EL/
├── .git/, .gitignore             Git repository (branch main) and its ignore list (see section 6)
├── CLAUDE.md                     Entry point for every new session (kept out of Git)
├── progress_log.md               Dated record of what was done and what passed
├── decisions_log.md              Dated record of decisions, deviations and open questions
├── pyproject.toml, uv.lock       Python 3.12 environment with pinned versions (.venv/ is the environment itself)
├── docs/                         Planning documents 01-10 (01-09 described in section 2; 10 is the Gate G1 report)
├── configs/                      prereg.yaml (draft evaluation values), data_version.yaml (pinned FlyWire data)
├── connectome/                   build_subgraph.py, analyze_subgraph.py, data/subgraph_v783/ (output), data/raw/ (downloads)
├── sim/                          env_check.py (simulator smoke test)
├── demo/                         pitch_figures.py (figures for the pitch)
├── fly/, models/, eval/          READMEs only so far (code arrives in Phases 4-12)
├── tests/                        test_environment.py, test_subgraph.py, test_analyze_subgraph.py
├── notebooks/figures/            circuit_subgraph.png, looming_frames.png, subgraph_weights.png
├── logs/                         env_check.txt
├── Fly_Wired_AI_EL_Abstract_1.docx    Your abstract
├── FlyPilot_EL_Phase1.pptx            The original pitch deck (15 slides)
└── FlyPilot_EL_Phase1_v2.pptx         Deck with speaker notes and progress slides (18 slides)
```

Real FlyWire data has been downloaded and the looming subgraph built. No circuit has been simulated yet and nothing has been trained.

---

## 2. What each existing file is for

### CLAUDE.md — the session entry point
Read this first when starting any new Claude session. It contains the working rules (stay in this folder, ask one decision at a time, never claim results that do not exist), the one-paragraph project summary, the file index and the deadlines. Whenever a new session starts, this is the file that restores context.

### 01_project_overview.md — what the project is
- **Problem:** small drones need fast obstacle detection on little compute.
- **Biology:** the fruit fly escape circuit (T4/T5 → LPLC2/LC4 → giant fiber).
- **Idea:** rebuild that circuit in software and use it as a drone's vision.
- **Hypothesis:** worded as a hypothesis, never a claim. Scope: one task, in simulation.
- **Comparisons and demo:** the four models and the side-by-side race.
- **Course fit and citations.**

### 02_locked_decisions.md — the settled design
27 numbered decisions, grouped into circuit, front end, controls, simulation, evaluation, demo and timeline. Each has its reason. These are not reopened unless you ask. If a question comes up in the viva ("why did you choose X?"), the answer is usually in this file.

### 03_implementation_plan.md — the architecture in brief
The pipeline diagram (camera frame → front end → LIF circuit → giant fiber → dodge), the planned repo layout, and the first build order. It is the short version; 07 is the full plan.

### 04_evaluation_protocol.md — the pre-registered test
The rules fixed before any result exists: the four models, the episode types, the metrics (TTC at trigger, false-alarm rate, dodge success), the data-efficiency sweep, the match rule, the five robustness shifts, the shuffle test, and the declared limitations. If a result is reported, it must follow these rules exactly. Any change must be written down as a deviation.

### 05_pitch_and_report_plan.md — the presentation
The deck order (problem → biology → FlyWire → idea → pipeline → comparisons → metrics and hypothesis → race → timeline → fit to course), the report outline, and the speaker notes, including the interpretation for each possible outcome.

### 06_open_items.md — what is still unresolved
- The abstract-vs-plan table: where your abstract differs from the locked plan (motion front end, dodge direction, sweep sizes, seeds, metrics). You need to decide how to handle it.
- Facts Claude still has to look up (FlyWire access, same-side input, transmitter counts, receptive-field extraction).
- Small open decisions (seed counts, angle thresholds, teammate roles).

### 07_phased_implementation_plan.md — the working plan
17 phases (0–16), each with dates, tasks, owners, acceptance checks and risks. Four decision gates (G1–G4) stop work until you sign off. Also contains the cut order, the standing risks and the collaboration protocol. This is the file to follow day by day.

### Fly_Wired_AI_EL_Abstract_1.docx — your abstract
Your original write-up: problem, biology, proposed solution, evaluation plan, conclusion and five references. It was written before the design review, so parts of it are out of date (see 06 section A). Treat it as the submitted-style summary, not the current design.

### FlyPilot_EL_Phase1.pptx — the pitch deck
Built from the RVCE EL Phase-I template: 15 slides covering the outline, introduction, literature review (a five-paper table plus a trends slide), problem, objectives, methodology (text plus a flowchart), outcomes, timeline, conclusion, references and thank-you. Picture slots are marked "[Insert picture]" for you to fill.

### .gitignore — what Git should not track
Excludes `CLAUDE.md`, documents 01-07 in `docs/`, the abstract and the original deck, plus the raw FlyWire downloads and `__pycache__/`. Documents 08 and 09, the v2 deck, the logs and all code are tracked. See section 6.

---

## 3. Planned folders and files (not yet created)

These come from `03_implementation_plan.md`, `07` Phase 1 and the logs planned in `07`.

**Status on 7 Nov:** `pyproject.toml`, `uv.lock`, all folders, both logs, `configs/prereg.yaml` (draft), `configs/data_version.yaml`, `connectome/build_subgraph.py` and `connectome/analyze_subgraph.py`, `fly/lif.py`, `configs/lif_params.yaml` and `sim/stimuli.py`, `fly/frontend.py` `fly/receptive_fields.py` and `fly/frontend_report.py` `fly/circuit.py` and `fly/calibrate.py` now exist. Still planned: `fly/*.py`, `models/*.py`, `eval/*.py`, `connectome/shuffle.py`, `sim/episodes.py` and the other simulation and demo files.

| Path | Created in | Will hold |
|---|---|---|
| `pyproject.toml` | Phase 1.3 | Pinned Python dependencies (PyTorch, NumPy, PyBullet, gym-pybullet-drones, pytest) |
| `connectome/` | Phase 1.1 | FlyWire fetch and subgraph code. `connectome/data/raw/` for downloaded data, not committed if large |
| `fly/` | Phase 1.1 | Fly pipeline: `frontend.py` (Reichardt motion detector), `lif.py` (neuron and synapse model), `circuit.py` (wiring LPLC2/LC4 to giant fibers), `calibrate.py` (the one global scale) |
| `sim/` | Phase 1.1 | Simulation: `episodes.py` (scripted generator), `render.py`, `drone_env.py`, `dodge.py` (sidestep) |
| `models/` | Phase 1.1 | Baselines: `cnn_scratch.py`, `resnet_temporal.py`, `train.py`, `tuning.py` |
| `eval/` | Phase 1.1 | Scoring: `metrics.py` (TTC, false alarms), `sweeps.py`, `robustness.py`, `plots.py` |
| `demo/` | Phase 1.1 | Race: `race.py`, `overlay.py` |
| `configs/` | Phase 1.1 / 1.6 | `prereg.yaml` (evaluation values, draft until Phase 8), `lif_params.yaml` (Phase 4), `data_version.yaml` (Phase 2) |
| `tests/` | Phase 1.1 / 1.5 | Pytest tests, one set per module |
| `notebooks/` | Phase 1.1 | Exploration and figures, e.g. `01_subgraph_summary.ipynb` |
| `logs/` | Phase 1.1 | Environment checks and run logs, e.g. `env_check.txt` |
| `progress_log.md` | Phase 1.7 | Dated record of what was done each session |
| `decisions_log.md` | Phase 1.7 | Dated record of every decision and deviation |

---

## 4. Components glossary

### Biology
- **Fruit fly escape:** the fly jumps away from a looming object (a swatter) within milliseconds.
- **T4/T5 neurons:** detect directional motion in the fly's visual system.
- **LPLC2 and LC4 neurons:** respond selectively to objects expanding towards the eye (looming). They are the circuit's inputs.
- **Giant fiber (GF):** one large neuron on each side of the fly. Its spike triggers the escape jump. In our design, the first GF to spike gives the threat's side, and the drone dodges the other way.
- **Looming:** an object growing in the visual field, the signal of a collision course.
- **FlyWire:** a synapse-level wiring diagram of the whole adult fly brain. Our circuit's wiring comes from it.
- **Synapse count:** how many synapses connect two neurons. It sets the connection strength.
- **Neurotransmitter:** the chemical a neuron releases. In FlyWire it is predicted per neuron. Acetylcholine (ACh) excites; GABA and glutamate (Glu) inhibit. Other transmitters are dropped and listed as a limitation.
- **flyvis:** an existing connectome-constrained model of the fly visual system (Lappalainen et al., 2024). Its parameters are trained, so it is an optional variant only.

### Fly pipeline (engineering)
- **Reichardt-style motion detector:** a fixed, untrained front end. It compares brightness at neighbouring points over time to detect motion direction, on a coarse grid.
- **LIF (leaky integrate-and-fire) neuron:** a simple spiking neuron. Input charges a membrane; when it crosses a threshold the neuron spikes and resets. Membrane time constant, threshold and reset come from published ranges and are not tuned.
- **Global scale:** the single tuned number. Every connection weight equals synapse count × this scale. It is tuned once on a separate calibration set, then frozen.
- **Calibration set:** about 30 episodes used to tune the global scale and the trigger. This is the fly's entire "training data".
- **Trigger:** the moment the fly circuit decides to dodge. For the fly, it is the first giant-fiber spike.
- **Degree-preserving shuffle:** rewires the connections while keeping each neuron's in-degree and out-degree, the total synapse count and the signs. It is the control: only "who connects to whom" changes. Based on the configuration-model idea.

### Comparisons and metrics
- **From-scratch CNN (primary baseline):** a small convolutional network trained on the same episodes. Input is 6 greyscale frames (about 0.5 s at 30 fps, every 3rd frame), full resolution.
- **Pretrained ResNet-18 + temporal head (secondary):** a frozen ImageNet ResNet-18 run on each frame, with a small temporal head on top to learn motion.
- **Time-to-collision (TTC) at trigger:** how many seconds before impact the model first triggers. Bigger means earlier warning.
- **False-alarm rate (FA):** how often a model triggers on a harmless passing or receding object. Every model's threshold is set to ≤5% FA on a shared set of about 100 no-dodge episodes.
- **Dodge success:** the drone dodges, on the correct side, without a collision.
- **Data efficiency:** how the result changes with 10, 30, 100, 300 and 1000 training episodes.
- **Match rule:** a CNN "matches" the fly if its mean TTC lies inside the fly's 95% interval. If no match by 1000 episodes, we say "didn't match within 1000".
- **Robustness:** frozen models tested on five shifts (contrast, noise, motion blur, new background texture, non-approaching distractors) at three severities each.
- **Shuffle rank:** where the real circuit falls in the shuffled distribution (e.g. "beats 95% of shuffles").
- **Pre-registration:** the evaluation rules are fixed in writing before results exist. A loss counts as a finding.

### Engineering and tools
- **gym-pybullet-drones:** the drone simulator (PyBullet physics, Python API).
- **Scripted episode generator:** creates each test episode from a seed: one object, varied speed, size, angle and side, with exact known TTC.
- **Seeds and disjoint sets:** each random seed fixes an episode. Calibration, training, threshold and test seeds never overlap, so no model sees test data.
- **Gate:** a checkpoint (G1–G4) where work stops until you sign off.
- **Cache:** rendered episodes saved to disk, keyed by seed and generator version.
- **Colab A100:** cloud GPU for CNN training. The RTX 3050 laptop handles the circuit and simulation.

---

## 5. How the parts connect

```
Camera frame (30 fps, from gym-pybullet-drones)
   │
   ├─► Reichardt front end (fixed)           fly/frontend.py
   │      └─► LPLC2/LC4 inputs, left and right halves
   │
   ├─► LIF circuit: LPLC2/LC4 → GF           fly/lif.py + fly/circuit.py
   │      weights = synapse count × global scale (fly/calibrate.py)
   │      first GF spike = trigger; side = which GF fired
   │      shuffled copy: same, with rewired connections (connectome/shuffle.py)
   │
   ├─► From-scratch CNN (6-frame stack)      models/cnn_scratch.py
   ├─► Frozen ResNet-18 + temporal head      models/resnet_temporal.py
   │      both output: trigger, left/right
   │
   ▼
Same fixed sidestep in the simulator          sim/dodge.py
   ▼
Scoring: TTC at trigger, FA rate, dodge success     eval/metrics.py
   ▼
Sweeps, robustness, plots                     eval/sweeps.py, robustness.py, plots.py
   ▼
Race demo with neuron overlay                 demo/race.py, overlay.py
```

**Rules that hold across the pipeline:**
- The front end and the scale are identical for the real and shuffled circuits.
- Every model's dodge is the same maneuver, so only the decision differs.
- Thresholds come from the shared no-dodge set and nowhere else.
- Test seeds are never used for calibration or training.

---

## 6. Things you should know about the repository

1. **Some documents are deliberately kept out of Git.** `.gitignore` excludes `CLAUDE.md`, documents 01-07 in `docs/`, the abstract and the original deck. Changes to those files do not show in `git status` and are not backed up by Git. Documents 08 and 09, the v2 deck, the logs and all code are tracked.
2. **You make every commit.** After each finished sub-stage I give you a ready-to-paste commit message and say which files it covers, including any changed file that Git ignores.
3. **A compiled file is tracked by mistake:** `tests/__pycache__/test_environment.cpython-312-pytest-9.2.0.pyc` was committed before `__pycache__/` was ignored. Fix: `git rm --cached -r tests/__pycache__`, then commit.
4. **A stray empty folder** I created earlier at `Sem 3/EL/Bio_Insp_EL` is no longer on disk. Nothing is left to clean up.
5. **The Git author** on the commit is `pavanshenoy21`, which is a different name from the one in the abstract. This matters only if commits are shared publicly.

---

## 7. Reading order to learn the project

1. **CLAUDE.md** (5 min): the rules and the map.
2. **01_project_overview.md** (10 min): what and why.
3. **02_locked_decisions.md** (20 min): read all 27, and check each reason.
4. **04_evaluation_protocol.md** (15 min): how success is measured.
5. **03_implementation_plan.md** (10 min): how the code will be organised.
6. **07_phased_implementation_plan.md** (30 min): the schedule and the gates.
7. **05_pitch_and_report_plan.md** (10 min): how it will be presented.
8. **06_open_items.md** (10 min): what is still unknown.

---

## 8. Self-check: can you explain these?

If you can answer each in your own words, you know the project.

1. Why is there one global scale, and not one per neuron?
2. What does the degree-preserving shuffle keep the same, and what does it change?
3. Why is TTC at trigger reported only at ≤5% false alarms?
4. Why is the fly's "30 calibration episodes" not the same as "zero training"?
5. Why was flyvis made optional?
6. What does "the first giant fiber to fire" decide, and why does it matter for the shuffle test?
7. What would it mean if the real circuit ties the shuffled circuits?
8. Why are the pre-registered values written down before any sweep runs?
9. What does Gate G1 check, and what happens if it fails?
10. Why does the CNN get a 6-frame stack rather than one image?

Answers are in 02 (decisions 1–27), 04 (metrics and match rule) and 07 (gates).
