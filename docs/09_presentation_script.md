# 09 — Presentation guide and script (Phase I pitch)

Read in this order: **Part 1** (understand it), **Part 2** (words you must know), **Part 3** (the script, slide by slide), **Part 4** (questions they will ask), **Part 5** (checklist for tomorrow).

The matching deck is `FlyPilot_EL_Phase1_v2.pptx`. It has the same script in the speaker notes of every slide.

---

## Part 1 — The whole project in plain words

**The one-sentence version.** A fruit fly dodges a swatter because it has a tiny wiring circuit built for exactly that job. Scientists have mapped that wiring. We copy the real wiring into software, put it in the "eyes" of a simulated drone, and test whether it dodges better than normal AI.

**Step by step**

1. **The fly's trick.** When something rushes towards you, it grows bigger in your vision, faster and faster. That growing is called **looming**. A fly has special neurons that fire only for looming. They connect to one big neuron, the **giant fiber**. When the giant fiber fires, the fly jumps away. That is the escape reflex.
2. **The map.** A **connectome** is a wiring diagram of a brain: every neuron and every connection. **FlyWire** is the connectome of a whole adult fly brain, about 140,000 neurons and over 50 million connections (synapses). It is public.
3. **Our idea.** Take the looming neurons and the giant fiber from that map, and rebuild them as a small program. Feed it what a drone's camera sees. When the giant fiber "fires", the drone dodges.
4. **Why this is interesting.** Normal AI for vision (a **CNN**) learns from thousands of labelled examples and can be fooled when lighting or backgrounds change. The fly's circuit comes already built. It needs almost no training. Maybe it warns earlier, needs less data, and copes better with change. We don't know yet. **That is the experiment.**
5. **The fair test.** We compare four things:
   - the **real** fly circuit,
   - the same circuit with its wires **scrambled** (the "shuffled" control),
   - a CNN trained from scratch,
   - a CNN that starts from a pretrained model (secondary).
   If the real wiring beats the scrambled wiring, the wiring itself matters, not just the idea of "a small circuit".
6. **The demo.** Two simulated drones, one with the fly circuit and one with the CNN, fly the same course while objects come at them. You see the fly neurons light up just before each dodge.

**Where we are:** this is the idea stage, so there are **no results yet**. We have set up the tools and pulled the real wiring data, and we checked that the circuit exists in it. Say this clearly. Never imply that the fly circuit already beat anything.

### Two comparisons that make it click
- **The giant fiber is like a fire alarm** wired to a sensor that only reacts to "something big growing fast". Not a camera and a brain, just a sensor wired to a trigger.
- **The shuffled control is like the same orchestra with the sheet music scrambled.** Same players, same number of notes, wrong order. If the real music sounds better, the order matters.

---

## Part 2 — Words you must know

| Word | Plain meaning |
|---|---|
| **Looming** | Something growing quickly bigger in your view, because it is coming straight at you. |
| **Neuron / synapse** | A brain cell / a connection between two brain cells. |
| **Giant fiber (GF)** | One very large neuron per side of the fly brain. When it fires, the fly jumps. Our "dodge now" signal. |
| **LPLC2, LC4** | Two kinds of neurons that react to looming. They connect to the giant fiber. Our circuit's inputs. |
| **T4/T5** | Neurons that detect which direction something moves. Earlier in the visual chain. |
| **Connectome / FlyWire** | A complete wiring diagram of a brain / the public one for the fruit fly. |
| **Spiking neuron (LIF)** | A simple model of a neuron: it collects input like a bucket filling, and when full it fires one spike and empties. "Leaky integrate-and-fire". |
| **Reichardt detector** | A simple fixed trick for detecting motion by comparing what a spot saw a moment ago with what its neighbour sees now. Our fixed "eye" stage. Nothing learned. |
| **CNN** | The standard kind of AI that looks at images. Needs lots of examples to learn. |
| **Trained from scratch** | Starts knowing nothing, learns only from our examples. |
| **Pretrained (ResNet-18)** | Starts already knowing general image features, then adapted. Our second CNN. |
| **Time to collision (TTC)** | How many seconds are left before the object hits. |
| **Early warning (TTC at trigger)** | How much time was left when the model first said "dodge". More time left means better. |
| **False alarm** | Saying "dodge" for something harmless, like an object that just passes by. |
| **Shuffled wiring** | Same neurons and same number of connections, but who connects to whom is scrambled. |
| **Pre-registered** | We fix the rules of the test in writing before we see any results, so we cannot pick rules that flatter us. |
| **Simulation (PyBullet)** | A physics program that flies the drone and renders what its camera sees. |

---

## Part 3 — The script, slide by slide

Speak slowly. Pause after each slide. The times add up to about 12 minutes. If you have less, shorten slides 4, 5 and 7 and skip slides 2 and 16 (that saves about 2 minutes).

**Total: about 12 minutes (700 seconds).**

### Slide 1 — Title (about 15 seconds)

**Say:**

> Good morning, everyone. We are Pavan, Pranav and Pratham, and our project for Bio-Inspired Engineering is called FlyPilot: giving a drone the escape reflex of a fruit fly.

**Tip:** Say the names clearly. Don't read the slide.

### Slide 2 — Outline (about 10 seconds)

**Say:**

> I'll go through nine parts: the idea, what the research says, the problem, our objectives, how we will do it, what we expect, the timeline, and our conclusion.

### Slide 3 — Introduction (about 60 seconds)

**Say:**

> Think about swatting a fly. It is gone before your hand arrives. It is not thinking about it. It has a tiny circuit in its brain built for one job: notice something growing quickly bigger in its vision, and jump.
>
> Here is the chain. Motion-sensing neurons feed two kinds of neurons, called LPLC2 and LC4, that react to things growing bigger. Those connect to one big neuron called the giant fiber. When the giant fiber fires, the fly jumps.
>
> Now think of a small drone. It also has to dodge things fast, but on a tiny computer. The usual solution, a CNN, needs thousands of labelled examples, is heavy to run, and often fails when lighting or backgrounds change.
>
> Our idea is to copy the fly instead. And we can do it properly, because scientists have published the fly brain's complete wiring diagram, called FlyWire. So we copy the real connections, not a guess.

**Tip:** If you add the fly picture, point at it while you describe the swat.

### Slide 4 — Literature review: five papers (about 90 seconds)

**Say:**

> These are the five papers we build on, in the order of the table.
>
> Von Reyn and colleagues, 2014: they showed that the timing of the giant fiber's spike decides how the fly escapes. That is the trigger we model.
>
> He and colleagues, 2016: they introduced ResNet, a standard image-recognition network. We use that family as one of our comparisons.
>
> Klapoetke and colleagues, 2017: they showed that LPLC2 neurons respond specifically to things expanding towards the eye. That is our input.
>
> Dorkenwald and colleagues, 2024: this is the FlyWire wiring diagram itself, about 140,000 neurons and over 50 million connections. This is where our wiring comes from.
>
> Lappalainen and colleagues, 2024: they built a model of the fly's visual system from the same wiring. It is related prior work and we cite it.
>
> So: two papers give the biology, one gives the wiring, one is related work, and one is the standard AI we compare against.

**Tip:** Don't read the table. Point to each row as you mention it.

### Slide 5 — Literature review: trends (about 40 seconds)

**Say:**

> Three points from reading these. First, whole-brain wiring diagrams now let us build models from real wiring. Second, looming detection and the escape are understood neuron by neuron. Third, CNNs are still the default for vision, but they need a lot of data.
>
> Our framework is bio-inspired engineering: take something evolution built for one task and test it in a machine. The scrambled-wiring control is how we check whether the exact wiring matters.
>
> One honest note. We have not found a study that does exactly this combination, but our search is not finished, so we say 'we have not found', not 'it does not exist'.

### Slide 6 — Problem definition (about 45 seconds)

**Say:**

> The problem. Small drones need to see and dodge sudden obstacles in a fraction of a second, with very little computing power. The standard CNN approach needs a lot of data, is heavy, and breaks when conditions change.
>
> The fly solves this with a tiny circuit, and we now have its wiring. What is not known is whether that wiring, rebuilt in software, actually gives an engineering advantage.
>
> Without a controlled test, 'bio-inspired' is just a claim. Our scrambled-wiring control, and rules fixed in advance, turn it into a test.

### Slide 7 — Objectives (about 45 seconds)

**Say:**

> Our main objective: build a fixed circuit from the real wiring, and test it as the vision of a simulated drone, against scrambled wiring and CNNs.
>
> Three specific steps. One: pull the looming circuit out of FlyWire and run it as a spiking network. Two: compare it with scrambled wiring and two CNNs on early warning, data efficiency and robustness. Three: show a side-by-side drone race, with the fly neurons firing before each dodge.
>
> What we hope to contribute is a reproducible test of whether real wiring carries useful structure, with open code. Either answer is useful.

### Slide 8 — Methodology (about 60 seconds)

**Say:**

> Our method is a simulation experiment. A fixed motion detector, with nothing learned, turns camera frames into signals. Those drive a spiking circuit wired from FlyWire, where each connection's strength is its synapse count times one single number.
>
> There are two giant fibers, left and right. Whichever fires first tells us the threat is on that side, and the drone dodges the other way.
>
> We generate test scenes in the drone simulator: objects that approach, pass by, or move away, with the exact time to collision known. We keep separate sets of scenes for calibration, training and testing.
>
> We measure how much warning each model gives, at the same small false-alarm rate. We train the CNN on 10 up to 1,000 examples, test five kinds of change like noise and blur, and run twenty or more scrambled versions.
>
> Tools: Python, PyTorch, PyBullet, on a laptop GPU and Colab.

**Tip:** If you add the simulator screenshot, point to the drone and the incoming object.

### Slide 9 — Methodology: the flowchart (about 75 seconds)

**Say:**

> Here is the whole system. The top row is the fly pipeline. The camera frame, 30 frames a second, is split into a left half and a right half. The fixed motion detector turns frames into movement signals. The spiking circuit, wired from FlyWire, receives them. The first giant fiber to fire is the trigger, and which side it is on tells us which way to dodge.
>
> The bottom row is the CNN. It looks at the last six frames and outputs 'dodge or not' and 'left or right'. We set every model's trigger so it gives false alarms at most 5% of the time, so the comparison is fair.
>
> Both rows end in the same fixed sidestep, so the only difference is the decision. At the bottom is what we measure. The fly row is run with real wiring and with twenty or more scrambled versions.

**Tip:** Walk left to right with your hand or pointer. This is the slide people look at longest.

### Slide 10 — Progress so far (about 60 seconds)

**Say:**

> We have already done the first technical steps. The software environment is set up, and the drone simulator runs and can produce camera frames.
>
> We downloaded the real FlyWire wiring data and checked it against published checksums. In that data we found the neurons we need: 210 LPLC2 neurons, 104 LC4 neurons, and two giant fibers, one on each side.
>
> We extracted the circuit. 293 of those neurons connect directly to the giant fibers, through 1,885 synapses. Every one of those connections stays on the same side as its giant fiber, which supports our left-right dodge rule.
>
> We also learned a limit. These neurons supply only about a fifth of the giant fiber's input, so our circuit models the looming pathway, not the whole giant fiber.
>
> The next step is to run this circuit on a simulated looming object.

**Tip:** State plainly that there are no performance results yet.

### Slide 11 — The real circuit (about 30 seconds)

**Say:**

> This is the real wiring we pulled from FlyWire. Each dot is one neuron. The navy ones are LPLC2 neurons, the red ones are LC4 neurons, and the yellow circle is the giant fiber, the neuron that triggers the escape. Thicker lines mean more synapses.
>
> On the left side, 94 LPLC2 and 54 LC4 neurons connect to the left giant fiber. On the right side, 95 and 50 connect to the right one. Nothing crosses sides, which is why the left and right giant fibers can tell us which way to dodge.
>
> This is the actual data, not a diagram we drew by hand.

**Tip:** Say it is the wiring only. No neuron has been simulated yet.

### Slide 12 — What the drone sees (about 30 seconds)

**Say:**

> This comes from our drone simulator, running on a laptop. The drone's camera looks forward and an object comes towards it. Watch how the object grows. At four metres it covers about 600 pixels, at two and a half metres about 1,550, at one and a half about 4,400, and at under a metre about 12,900.
>
> It does not grow steadily. It grows faster and faster. That accelerating growth is exactly what looming neurons are built to detect, and it is the input our fly circuit will receive.

**Tip:** Say 'simulator'. No circuit has seen these frames yet.

### Slide 13 — Proposed outcomes (about 45 seconds)

**Say:**

> What do we expect? Our hypothesis is that the real circuit triggers earlier than scrambled wiring, and matches or beats a CNN trained from scratch on early warning, data efficiency and robustness, especially when training data is small. This is one task, in simulation, and nothing more.
>
> If it works, it is evidence that evolved wiring carries useful structure, and a light, data-efficient idea for small drones. Next steps could be real cameras, other fly circuits, or neuromorphic hardware.
>
> We fix every comparison in advance, so a loss is a finding, not a failure.

**Tip:** Say 'hypothesis', not 'result'.

### Slide 14 — Timeline (about 30 seconds)

**Say:**

> Our timeline. This pitch completes the idea and setup phase. Early November: run the circuit on a synthetic looming object, with the scrambled control. Mid November: build the test scenes and fix the evaluation values. Late November: train the CNNs and run the experiments, with the drone loop in parallel. Early December: finish the experiments, plots and demo. Mid December: report, rehearsal, and a spare week.

### Slide 15 — Conclusion (about 30 seconds)

**Say:**

> To sum up. FlyPilot rebuilds the fruit fly's escape circuit from its real wiring, and tests it as a drone's vision against scrambled wiring and CNNs.
>
> Whether evolved wiring gives small machines faster, more data-efficient, more robust collision avoidance is a testable question, and the scrambled control isolates the answer.
>
> Next, we run the circuit on a looming object and build the drone simulation.

### Slide 16 — References (about 5 seconds)

**Say:**

> These are our references. I won't read them out, and I'm happy to discuss any of them.

### Slide 17 — Expected outcome by the end of the first year (about 20 seconds)

**Say:**

> By the end of the year we aim for a conference-style paper in IEEE format, an open-source release so others can reproduce the work, and a proposal to extend it to real cameras or other fly circuits.

### Slide 18 — Thank you (about 10 seconds)

**Say:**

> Thank you. We are happy to take questions.


---

## Part 4 — Questions they will ask, and honest answers

**Why a fruit fly?**
It is the only adult brain whose complete wiring diagram is public, and its escape circuit is small and well studied. That makes it possible to copy real wiring, not a guess.

**Why not just use a better CNN?**
We are not saying CNNs are bad. We are testing a specific question: when data is scarce or conditions change, does evolved wiring help?

**What have you actually done so far?**
Set up the software, tested the simulator, downloaded the real FlyWire data, and checked that the circuit we need exists in it: 210 LPLC2 and 104 LC4 neurons, two giant fibers, 293 of those neurons connecting directly to the giant fibers, all on the same side as their giant fiber. The circuit simulation itself is next.

**Does it work?**
We don't know yet, and we say so. We wrote the test rules down before running it, so a loss is a finding, not a failure.

**What is the shuffled control for?**
To separate "a small looming circuit" from "this exact wiring". If the real wiring beats the scrambled one, the wiring matters.

**Why spiking neurons and not an ordinary neural network?**
They are a closer copy of the real thing, and they let us show the fly neurons firing before each dodge, which makes the result visible in the demo.

**What if the CNN wins?**
Then we learn where hand-built biological circuits stop being competitive, and how much data a CNN needs to overtake them. That still answers our data-efficiency question.

**Why only 5% false alarms?**
Otherwise a model could "win" by dodging everything. Every model is allowed the same small false-alarm rate, then we compare how early each warns.

**Is this new?**
We haven't found a study that tests a connectome-wired looming circuit against shuffled wiring and CNNs in closed-loop drone flight. Our literature search is not exhaustive, so we say "we have not found", not "none exists".

**Isn't a simulation unrealistic?**
Yes. This is a first test in simulation. Real-camera flight is future work. We claim nothing about real drones.

**How much of the giant fiber's input does your circuit cover?**
About 20%. LPLC2 and LC4 are major looming inputs, but the giant fiber also gets input from other cell types we leave out. Ours is a model of the looming pathway, not of the whole giant fiber. We state that as a limitation.

**How is the fly circuit trained?**
It isn't, apart from one number (a global strength scale) tuned once on about 30 example episodes. The wiring is copied from the connectome. The CNN learns from 10 up to 1000 episodes, so we can measure how much data it needs.

**Who does what?**
*(Fill in with Pranav and Pratham before tomorrow. Don't claim work nobody has agreed to.)*

**Why LPLC2 and LC4 and not other circuits?**
They are the best-documented looming detectors that connect to the giant fiber, and they are small enough to finish this semester.

**What is a connectome, in one line?**
A wiring diagram of a brain.

---

## Part 5 — Checklist for tomorrow

- [ ] Open `FlyPilot_EL_Phase1_v2.pptx`. Check that it opens and the speaker notes show.
- [ ] Fill the four "[Insert picture]" boxes (slides 3, 5, 8, 13) or delete them. An empty dashed box on screen looks unfinished.
- [ ] Skim each literature-table summary (slide 4) against the paper's abstract. I wrote them from memory.
- [ ] Say it out loud once, with a timer.
- [ ] Decide the answer to "who does what" with Pranav and Pratham.
- [ ] Save a PDF copy of the deck as a backup.

### Things not to say
- "Our circuit works / beats the CNN." There are no results yet.
- Precise numbers for the fly's escape time. Say "a fraction of a second, faster than the swat". Quote a figure only if you have checked it.
- "Nobody has done this." Say "we haven't found it".
- "The whole giant fiber circuit." It is the looming pathway into the giant fiber (about 20% of its inputs).

### Numbers you can say safely
- FlyWire: about 140,000 neurons, over 50 million synapses.
- In our data: 210 LPLC2 neurons, 104 LC4 neurons, 2 giant fibers (one per side).
- 293 of those neurons connect directly to the giant fibers, through 1,885 synapses, every one on the same side as its giant fiber.
- Plan: CNN trained on 10, 30, 100, 300 and 1000 episodes; at most 5% false alarms; at least 20 shuffled versions.
