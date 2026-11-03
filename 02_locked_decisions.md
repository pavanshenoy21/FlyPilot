# 02 — Locked decisions (from the grilling session)

Format: decision — why. Reopen only if the user asks.

## Circuit
1. **Scope: LPLC2 + LC4 → giant fiber only.** Best-documented looming escape path; finishable by December. Wider scope adds risk without helping the comparisons.
2. **Model: leaky integrate-and-fire (LIF).** Gives the spiking "neuron activity before each dodge" visual a rate model can't.
3. **Weights = FlyWire synapse count × ONE global scale.** Signs from predicted neurotransmitter: ACh excitatory; GABA and glutamate inhibitory. Other transmitter types: connections dropped and listed as a limitation (count them once data is loaded).
4. **Nothing else tuned.** Membrane time constant, threshold, reset set once from published ranges. The global scale is tuned once on a separate stimulus set so the GF fires for looming but not for passing/receding objects, then frozen for all models and conditions.
5. **Two escape neurons, one per side.** Frame split into left/right halves, each driving its side's LPLC2/LC4 → GF. Whichever GF fires first gives the threat side; drone dodges the other way. When-and-which-way both come from the wiring, so the shuffle tests both. Nothing trained.
6. **Head-on threats:** test episodes are off-centre (a correct side exists). A separate head-on subset is reported on its own; dodging either side counts as correct there, same rule for CNNs.
7. **Check pending:** does each GF receive mostly same-side input in FlyWire? (needed to justify decision 5).

## Front end
8. **Fixed Reichardt-style motion detector on a coarse fly-like grid, no learning.** Keeps the fly pipeline's data budget honest (30 calibration episodes, nothing else learned). Shared by real and shuffled circuits.
9. **Receptive fields:** use connectome positions (lobula / lobula plate synapse locations) if extractable; otherwise tile evenly over the visual field using published sizes. State which was used.
10. **flyvis = optional labelled variant only** (its parameters were trained on optic-flow; pretraining must be declared). Cited as prior work either way.
11. **Declared simplification:** LC4 mostly takes lobula inputs, not T4/T5 directly; feeding it the same motion signal is a simplification. Same for LPLC2's non-T4/T5 inputs.

## Controls and baselines
12. **Shuffle:** degree-preserving rewire (configuration-model style): keeps each neuron's in/out degree, total synapse count, signs. 20+ seeds; report mean ± spread and the real circuit's position in the shuffled distribution (permutation-test style). Plot: real circuit marked on shuffled histogram.
13. **From-scratch CNN = primary baseline.** Small. 6 stacked greyscale frames, full-frame input (e.g. 128×128), two heads: dodge trigger + left/right. Record parameter count for the report.
14. **Time window:** camera 30 fps; window slides every frame (can trigger at any frame, like the fly); inside the window take every 3rd frame, 6 frames ≈ 0.5 s history (covers the expansion phase of 1–2 s episodes).
15. **Pretrained ResNet-18 = secondary (first to cut if time slips).** Frozen backbone run per frame (grey→3ch, no layer surgery), small temporal head (1D conv or GRU over 6 feature vectors) → two outputs. One rule at every data size. (An averaged-filter first layer was rejected: it would sum frames and lose the motion signal.)
16. **CNN tuning recipe (small, fair, frozen):** same grid for both CNNs — 3 learning rates × 2 weight decays, early stopping, 20% validation split taken *from within* each training budget (so "N episodes" means N). Honest admission: validation is noisy at 10–30 episodes. Low-res CNN check (fly's coarse grid) as an extra.
17. **Shared trigger-threshold set:** one fixed set of ~100 no-dodge episodes sets every model's trigger threshold to ≤5% false alarms, fly included. Declared shared; not counted in anyone's training budget.

## Simulation and data
18. **Simulator: gym-pybullet-drones** (light, Python, easy side-by-side).
19. **One scripted episode generator.** Single object per episode, varying speed, size, approach angle, start side. Types: approaching (must dodge), passing (near miss), receding. Exact TTC known. Calibration, CNN-training, validation, test sets use disjoint seeds. Cache episodes.
20. **Dodge maneuver:** one fixed-size sidestep, identical for all models. Wrong side = failed dodge.

## Evaluation (full detail in 04)
21. **Early warning:** TTC remaining at first trigger, evaluated at ≤5% false-alarm rate.
22. **Data efficiency:** CNNs trained on 10, 30, 100, 300, 1000 episodes (multiple seeds). Fly = flat line plus a marker at its true calibration size (30 episodes). Don't claim "zero data".
23. **"Match" rule (locked pre-results):** CNN matches the fly when its mean TTC at trigger is within the fly circuit's 95% interval at ≤5% false alarms. If no match by 1000 episodes, report "didn't match within 1000".
24. **Robustness:** train/calibrate clean only; test five shifts at three severities each: lower contrast, pixel noise, motion blur, new background texture, distractor objects that pass without approaching (most important).

## Demo and deliverables
25. **Race:** fly drone vs from-scratch CNN trained on 100 episodes; scripted fixed-seed sequence; hit drone is out; neuron-activity overlay.
26. **Pitch deck:** ~10 slides (see 05). Report 3–4 pages for Phase 1.
27. **Team on slides:** all three names; roles as placeholders.

## Timeline
- Before pitch (Nov 3): slides + short report + first FlyWire look (neurons, connections, transmitters, GF same-side input).
- Early Nov: LIF circuit + Reichardt front end on a synthetic looming dot, with shuffle control → Phase 2 artifact.
- Mid Nov: episode generator, cached episodes, pre-registered values written into report.
- Late Nov: CNN training and sweeps in background; drone closed loop in parallel.
- Early Dec: finish sweeps, plots, race dashboard.
- Mid Dec: report, rehearsal, a real buffer week.
- Cut order if slipping: flyvis variant → pretrained ResNet → extra robustness severities.
