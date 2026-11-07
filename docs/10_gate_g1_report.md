# 10 — Gate G1 report: is the looming circuit usable?

Date: 7 Nov 2026. Covers Phases 2 and 3 (sub-stages 2A–3C). Data: FlyWire snapshot 783.

## 1. Verdict (recommended)

**PASS, with decisions to confirm.** The giant fibers do receive input from LPLC2 and LC4 neurons on both sides, every one of those connections stays on its own side, the transmitter evidence supports excitatory connections, and the neurons' receptive-field positions can be recovered from the data. Nothing found so far breaks the design.

Two things are less comfortable than the plan assumed, and both go into the report as limitations:
1. LPLC2 and LC4 supply only about **20%** of each giant fiber's input synapses. Our circuit is a model of the looming pathway into the giant fiber, not of the whole giant fiber.
2. The right giant fiber receives **27% more** synapses from our neurons than the left, which can bias the "first giant fiber to fire" direction rule.

Whether the circuit actually fires the giant fiber for looming objects is **not** tested yet. That is Gate G2 (Phase 6).

## 2. The G1 criteria against the evidence

| Criterion (from `07_phased_implementation_plan.md`) | Evidence | Status |
|---|---|---|
| Each giant fiber receives LPLC2 / LC4 input | Left: 94 LPLC2 + 54 LC4 neurons, 832 synapses. Right: 95 LPLC2 + 50 LC4 neurons, 1,053 synapses. | Met |
| Input is on the giant fiber's own side (supports the two-giant-fiber direction rule) | 100% of synapses are same-side. No contralateral LPLC2 / LC4 input. | Met |
| ACh / GABA / glutamate cover most synapses | All 293 connections are from neurons with a known transmitter of acetylcholine (Davis et al. 2020, via the annotation file). None dropped. | Met, with a caveat (section 4, item 1) |
| Receptive-field method chosen | Sampled lobula synapse centroids (`progress_log.md`, 3B). Proposed, pending your confirmation. | Proposed |
| Fail condition: no usable LPLC2 / LC4 to giant fiber path | Not the case | Not triggered |
| Conditional condition: input mostly one-sided | Not the case | Not triggered |

## 3. What the circuit is, in numbers

- **Subgraph:** 295 nodes (2 giant fibers + 293 source neurons), 293 edges, 1,885 synapses. Built by `connectome/build_subgraph.py` from `connectome/data/raw/`; outputs in `connectome/data/subgraph_v783/`; hashes in `configs/data_version.yaml`.
- **Coverage:** every LC4 neuron (54 left, 50 right) connects directly to a giant fiber. 94 of 108 left and 95 of 102 right LPLC2 neurons do; 21 LPLC2 neurons have no direct connection and are left out.
- **Strength:** a connection is 1–16 synapses (mean 4.9–8.6 per neuron, depending on side and type). The input is spread: the strongest 10% of neurons hold only 17–27% of the synapses.
- **Share of the giant fiber's input:** 19–21%. The rest comes from other cell types (the largest are CB3707, DNp70, PVLP122b, SAD014), which the design leaves out.

## 4. Findings you should know about

1. **The transmitter evidence is neuron-level, and the per-connection predictions disagree.** `known_nt` (experimental) says acetylcholine for all 314 LPLC2 and LC4 neurons. The connection table's per-connection probabilities pick glutamate for 55% of our synapses and agree with the neuron-level label on only 33.6%, and the gap does not shrink on larger connections. We use the neuron-level label (decisions_log 13). Limitation to state.
2. **Left/right asymmetry.** The right giant fiber receives 1,053 synapses from our sources and the left 832. New check (`connectome/asymmetry_check.py`):

   | Synapses into the giant fiber from | Left | Right | Right / left |
   |---|---|---|---|
   | LC4 | 374 | 431 | 1.15 |
   | LPLC2 | 458 | 622 | 1.36 |
   | all other neurons | 3,495 | 4,094 | 1.17 |

   So the right giant fiber gets more input from everything, not only from our neurons; LPLC2 is the largest gap. Left source neurons also look less complete overall: median total input synapses are 1,207 (left LC4) against 1,382 (right), and 765 (left LPLC2) against 996 (right). This could be tracing completeness or biology; the data cannot tell which. The LPLC2 to giant-fiber gap (about 26%) is bigger than the LPLC2 neurons' overall output gap (about 8%).
3. **Weak connections.** Our table includes connections of 1–4 synapses, which FlyWire's own Codex tables drop. Dropping them would remove 48% of the left giant fiber's source neurons and 23% of the right's.
4. **Giant-fiber transmitter labels are unreliable** (right glutamate, left acetylcholine, confidence 0.27–0.32). Irrelevant here because we only read the giant fibers' spikes, but worth a sentence.
5. **Receptive fields.** Positions are recoverable (2% sample: every neuron covered, two halves agree to 5.2 µm against a 20–38 µm spread). Two steps remain for Phase 5.4: a larger sample (about 15%) and the conversion from a lobula position to a visual-field angle. Fallback: even tiling with published receptive-field sizes.
6. **Data licence.** The annotation file's repository has no confirmed licence (its LICENSE file returned 404). We cite the papers either way.
7. **Units.** The synapse table is in nanometres; the annotation file is in 4 × 4 × 40 nm voxels.

## 5. Decisions for you

| # | Question | Recommendation | If you choose otherwise |
|---|---|---|---|
| 14 | How to handle the left/right asymmetry | **Accept it for now and measure it in Phase 6.** Run symmetric looming stimuli through the calibrated circuit. If the right giant fiber fires first on more than 60% (or fewer than 40%) of symmetric trials, switch to one scale per giant fiber, tuned so symmetric stimuli give 50/50. Write this threshold into `prereg.yaml` now so it cannot be chosen after seeing results. | One scale per side from the start adds a tuned number (changes locked decision 3). Normalising each giant fiber's total input weight changes the wiring (against the point of the real-versus-shuffled test). |
| 15 | Keep connections of 1–4 synapses? | **Keep everything.** Weights scale with synapse count, so weak connections carry little weight anyway (they are about 24% of the left giant fiber's synapses and 8% of the right's). Run a 5-synapse version later as a sensitivity check. | Dropping them shrinks the left circuit to 77 neurons and widens the asymmetry. |
| 13 | Take transmitter signs from the neuron-level label? | **Yes** (rule: `known_nt` if present, otherwise `top_nt`). | Using per-connection probabilities would flip the sign of many connections and is contradicted by experimental evidence. |
| 19 | Receptive-field method | **Confirm** sampled lobula synapse centroids, with even tiling as the fallback. | Even tiling from the start is faster but is not from the connectome. |
| 18 | Remove the tracked `.pyc` file | `git rm --cached -r tests/__pycache__` | None. It is only housekeeping. |

## 6. Limitations to carry into the final report (draft wording)

- The circuit models the direct LPLC2 and LC4 inputs to the giant fibers, about 20% of their input synapses; other inputs are not included.
- Connection signs come from neuron-level transmitter labels (experimental for LPLC2 and LC4); per-connection predictions in the same data disagree and were not used.
- Left and right circuits differ in strength (right giant fiber receives 27% more synapses from LPLC2 and LC4), which may partly reflect tracing completeness.
- The receptive-field layout is estimated from a sample of synapse positions and an assumed mapping from lobula position to visual-field angle.
- All data comes from one brain (FlyWire snapshot 783); no across-animal variability is represented.

## 7. What happens next

If you accept the verdict, **Phase 4 (LIF core)** starts: a generic, tested leaky integrate-and-fire network. Its inputs are ready: `connectome/data/subgraph_v783/nodes.csv` and `edges.csv`. Gate G2 (Phase 6) will test whether the assembled circuit fires selectively for looming.
