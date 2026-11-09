# 11 — Shuffle control report: does the real wiring matter?

Date: 9 Nov 2026. Covers Phase 7, sub-stages 7.1 (shuffle, Gate G3) and 7.2 (20 shuffled circuits). Data: FlyWire snapshot 783. Stimuli: synthetic (`sim/stimuli.py`), not yet the drone simulator.

## 1. Verdict

**Gate G3 (is the control fair?): PASS.** The shuffled circuits keep every property we fixed in advance. Only who connects to whom changes.

**Result: on synthetic stimuli, the real fly wiring beats shuffled wiring.**
- **Dodge side:** the real wiring picks the correct dodge side 98% of the time. Shuffled wiring is at chance (47%). The real wiring beats all 20 shuffles.
- **Warning time:** the real wiring warns earlier (189 ms against 174 ms). It beats 19 of 20 shuffles, which falls just short of p < 0.05.
- **Detection:** every circuit, real or shuffled, catches every loom with no false alarms, so detection cannot tell them apart here.

The method, the scores and the predicted outcome were written into `configs/prereg.yaml` before any shuffled circuit was run.

## 2. What the shuffle is (7.1)

**Method** (locked decision 12; `fly/shuffle.py`; decisions_log 28). This is a configuration-model rewire:
- The list of connection targets is randomly reordered across connections.
- Each connection keeps its synapse count and the transmitter of the neuron it comes from.
- A draw that would create a duplicate or self-connection is redrawn.
- 20 wiring seeds are used (0–19). They are numbered separately from the stimulus seeds.

**What stays the same.** Each item below is checked by `tests/test_shuffle.py` for every one of the 20 seeds:

| Property | Kept? |
|---|---|
| Each neuron's number of outgoing and incoming connections | Yes |
| Each neuron's total output synapses | Yes |
| Total synapses (1,885) and the set of per-connection synapse counts | Yes |
| Sign counts, and each neuron's transmitter | Yes |
| No duplicate connections, no self-connections, same number of connections (293) | Yes |
| Neurons, receptive fields, motion front end, LIF constants | Shared with the real circuit |
| A deliberately broken shuffle is caught by the check | Yes |

**What a shuffle can change on this circuit.** In the real circuit, each of the 293 LPLC2/LC4 neurons has exactly **one** connection, and it always goes to the giant fiber on its **own side**. A rewire that keeps connection counts can therefore only change *which* giant fiber each neuron drives.

| | Real | 20 shuffles |
|---|---|---|
| Connections staying on their own side | 100% | 43–54% |
| Synapses into left / right giant fiber | 832 / 1,053 | 880–1,005 / 880–1,005 |

So in practice, this control tests whether the real left/right routing matters. It does not test finer structure, such as which LPLC2 neurons connect more strongly. We recorded this before running anything (`progress_log.md`, 7.1).

## 3. How the shuffles were run (7.2)

**Decision.** Each shuffle got the real circuit's tuning *procedure*, not its tuned *numbers* (decisions_log 29, Pavan's choice). Each wiring gets its own best shot, so the comparison is not tilted towards the real circuit. Each shuffle went through these steps (`fly/shuffle_eval.py`):

1. **Input gain.** The same calibration seeds (1000–1009 per kind), the same 25-value grid, and the same rule.
2. **Symmetry check.** Run on centred looms (seeds 3000–3039). If one giant fiber fired first on more than 60% or fewer than 40% of trials, a per-side gain split was tuned with the same grid, seeds (4000–4039) and rule. This fired for 13 of the 20 shuffles. It also fired for the real circuit.
3. **Held-out test.** 50 looming, 50 passing and 50 receding stimuli (seeds 2000–2049), scored as in Gate G2.
4. **Secondary run.** Every shuffle was also run on the held-out set at the real circuit's frozen gains (left 5.4778, right 5.7729).

**Chosen gains.** 15 shuffles got the same input gain as the real circuit (5.62) and 5 got 6.81. In total there were 33,240 circuit runs, which took 1 h 45 min on 12 CPU workers.

**Ranking.** For each score we report:
- the share of shuffles the real circuit beats (ties count half)
- a one-sided permutation p-value, (1 + shuffles at least as good) / 21

With 20 shuffles, the smallest possible p is 1/21 = 0.048.

## 4. Results

### Main analysis: each shuffle tuned by the same procedure

| Score (held-out) | Real circuit | Shuffles: mean ± SD (min–max) | Real beats | p |
|---|---|---|---|---|
| **Correct dodge side** (off-centre looms, \|x\| ≥ 0.02 m) | **97.8%** (45/46) | 47.1% ± 15.8 (15–76%) | 100% | **0.048** |
| **Median warning before impact** | **189 ms** | 174 ± 6 ms (166–189) | 95% | 0.095 |
| Looms caught | 100% (50/50) | 100% in every shuffle | tie | 1.0 |
| False alarms (passing + receding) | 0% (0/100) | 0% in every shuffle | tie | 1.0 |

### Secondary analysis: every shuffle at the real circuit's frozen gains

| Score | Real | Shuffles: mean ± SD (min–max) | Real beats | p |
|---|---|---|---|---|
| Correct dodge side | 97.8% | 48.2% ± 16.5 (15–80%) | 100% | 0.048 |
| Median warning before impact | 189 ms | 171 ± 2 ms (167–175) | 100% | 0.048 |

Per-shuffle numbers are in `logs/shuffle_per_seed.csv`.

## 5. What it means

1. **Dodge direction comes from the wiring.** This was predicted in advance. Shuffled circuits still detect the loom, but each giant fiber now collects about half its input from the wrong eye, so which one fires first is close to a coin flip.
   - The spread across shuffles (15–76%) partly tracks how many connections happened to stay on their own side (correlation 0.6 across the 20 shuffles).
   - Even the best shuffle (76%) is well below the real circuit (98%).
2. **The real wiring also warns earlier.** This was **not** predicted; we had expected timing to change little.
   - At equal gains, all 20 shuffles are slower, by 14–22 ms.
   - After each shuffle's own tuning, one shuffle (seed 7, which was tuned to a higher gain) matches the real circuit at 189 ms. So the timing result has p = 0.095 in the main analysis.
   - We report it as **suggestive, not established**.
   - Why it happens is not yet explained. A likely cause: when each giant fiber listens to only one eye, it gets a cleaner build-up of signal from that side. This is a hypothesis to check, not a finding.
3. **Detection is at ceiling.** Every circuit catches every synthetic loom with no false alarms. This says the synthetic set is easy, not that the wiring is irrelevant to detection. The simulator episodes (Phase 8 onwards) are harder and may separate them.

## 6. Limitations (to state in the report)

- **Synthetic stimuli only.** These are a single dark sphere on a plain background, so they are easier than the drone simulator episodes. The main pre-registered comparison is still to come.
- **The control is narrow on this circuit.** Because every neuron has one same-side connection, the shuffle can only test left/right routing. A stronger control would need a different design. Locked decision 12 does not include one.
- **20 shuffles** limit p to at least 0.048. More shuffles would sharpen the timing result. Each extra shuffle costs about 5 minutes of computing.
- **Two tuned numbers per circuit** (the gain and the left/right split). Both are tuned the same way for real and shuffled circuits.
- **Citations written from memory** in earlier phases (5° facet spacing, LPLC2 receptive field size) are still unverified. They affect the front end, which is shared by all circuits, not this comparison.

## 7. Files

| File | What it holds |
|---|---|
| `fly/shuffle.py`, `tests/test_shuffle.py` | Rewire, the preservation checks (Gate G3), 25 tests |
| `fly/shuffle_eval.py`, `tests/test_shuffle_eval.py` | Per-shuffle tuning and testing, ranking, 4 tests |
| `configs/prereg.yaml` → `shuffle:` | Method, seeds, procedure, scores, expectation, result hash |
| `logs/shuffle_wiring_summary.csv` | Same-side share and giant-fiber input per shuffle |
| `logs/shuffle_calibration_runs.csv`, `logs/shuffle_heldout_runs.csv` | Every run (15,000 and 6,520 rows) |
| `logs/shuffle_per_seed.csv`, `logs/shuffle_result.json` | Per-shuffle scores and the summary above |
| `decisions_log.md` 28–29, `progress_log.md` 7.1–7.2 | Decisions and dated record |

**Still to do in Phase 7:**
- **7.3:** the histogram figure for the slides, showing the shuffles' scores with the real circuit marked.
- **7.4:** the Phase II "what we've built" summary.
