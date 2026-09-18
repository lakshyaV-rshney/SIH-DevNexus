# SIH 2026 — Problem Statement 26055
## Smart Scan Strategy for Electronic Warfare

> **Purpose of this document:** A detailed, team-ready interpretation of SIH Problem Statement **26055**, including what the statement means, what must be built, what should be demonstrated, suggested architecture, evaluation metrics, datasets, risks, and a practical implementation plan.
>
> **Important:** The official problem statement should remain the authority for submission requirements. Some third-party SIH mirrors currently disagree on metadata such as the submission deadline; verify the live SIH portal before submitting.

---

## 1. Problem at a glance

| Field | Value |
|---|---|
| **Problem ID** | SIH26055 / 26055 |
| **Title** | Smart Scan strategy for Electronic Warfare |
| **Organization** | Defence Research and Development Organisation (DRDO) |
| **Department** | Department of Defence Production / IDEX |
| **Track** | Software |
| **Theme shown by current SIH mirrors** | Robotics and Drones |
| **Core domain** | Electronic Support / spectrum surveillance |
| **Core technical problem** | Decide **where and when a receiver should scan** when the transmitter/emitter situation is initially unknown |
| **Primary AI task** | Learn an adaptive scan/scheduling policy from observations, hits and misses |
| **Primary objective** | Reduce intercept time while maintaining a high interception rate |
| **Required environment** | A simulated RF environment with known ground truth for emitter activity |
| **Expected solution named in PS** | Machine-learning-based Electronic Support receiver scheduler software |

### One-sentence interpretation

**Build a simulator of a changing RF environment and an intelligent scheduler that learns which frequency band to observe next, instead of blindly sweeping all bands in a fixed open-loop order.**

---

# 2. What the problem statement actually means

The statement is difficult mainly because it uses Electronic Warfare terminology.

At its core, this is a **sequential decision-making problem under uncertainty**.

Imagine a receiver that can listen to only a small part of a very large frequency spectrum at one instant.

There may be many frequency bands:

```text
Total spectrum
┌────┬────┬────┬────┬────┬────┬────┬────┐
│ B1 │ B2 │ B3 │ B4 │ B5 │ B6 │ B7 │ B8 │ ...
└────┴────┴────┴────┴────┴────┴────┴────┘
        ↑
   receiver can
   inspect only a
   limited portion
```

The receiver has to repeatedly choose:

> **Which band should I look at now?**

and, because emitters can change over time:

> **When should I look at that band?**

That creates the two dimensions mentioned by the statement:

1. **Frequency dimension** — which band to inspect.
2. **Time dimension** — when to inspect it.

A fixed sweep might do:

```text
B1 → B2 → B3 → B4 → B5 → B6 → B7 → B8 → repeat
```

The problem asks whether a smarter system can learn something like:

```text
B1 → B4 → B4 → B7 → B2 → B4 → B8 → B4 → ...
```

when the observations indicate that some bands are more likely to contain useful transmissions at particular times.

The important point is that the scheduler is **not simply predicting whether a band is active**.

It is using predictions to make a **decision about the next observation**.

---

# 3. Why a normal fixed scan is insufficient

The statement describes existing/open-loop strategies as being based on pre-mission or prior information.

A simple strategy prioritizes:

> Scan the entire spectrum as quickly as possible.

That sounds reasonable, but it creates a problem.

Suppose there are 100 bands and the receiver spends equal time on every band.

If an important emitter appears immediately after the receiver passes that band, the receiver may not return for a long time.

At the same time, the receiver may repeatedly spend time looking at:

- empty bands,
- non-threatening transmissions,
- bands whose activity is already well understood.

Therefore, two receivers with exactly the same hardware can have very different performance simply because one chooses **better scan decisions**.

### The opportunity

Use previous observations to estimate:

- which bands are likely to be active,
- which bands are changing,
- how reliable those estimates are,
- how long it has been since a band was observed,
- how useful another observation of that band is likely to be.

Then schedule the next observation accordingly.

---

# 4. Important terminology

## 4.1 Emitter

An **emitter** is a source producing an RF transmission.

For the simulation, you do not need to model a real-world military emitter.

Represent an emitter abstractly using properties such as:

```text
Emitter
├── ID
├── frequency/band
├── active/inactive state
├── activity pattern
├── start time
├── duration
├── possible movement across bands
└── optional signal characteristics
```

For an SIH prototype, synthetic emitters are preferable because the statement explicitly calls for a simulated RF environment with ground truth.

---

## 4.2 Receiver

The receiver is the simulated sensor that decides what portion of the spectrum to inspect.

A simplified receiver model can be:

```text
Receiver
├── available frequency bands
├── instantaneous bandwidth
├── scan action
├── dwell/observation time
├── detection probability
├── false-alarm probability
└── observation history
```

You are not required to reproduce a classified DRDO receiver.

The objective is to model the **decision problem**.

---

## 4.3 Open-loop scanning

An open-loop scanner follows a predetermined schedule.

Example:

```python
for band in bands:
    observe(band)
```

It does not substantially change its scan decision based on what it just observed.

This is your most important baseline.

---

## 4.4 Smart/adaptive scanning

An adaptive scanner observes the environment and changes its next action.

Conceptually:

```text
Observation
     ↓
Update belief/model
     ↓
Estimate usefulness of candidate bands
     ↓
Select next band
     ↓
Observe
     ↓
Record hit/miss
     ↓
Update model
     ↓
Repeat
```

This closed feedback loop is the heart of the project.

---

# 5. What DRDO is asking you to build

The expected solution is:

> **Machine learning based Electronic Support receiver scheduler software.**

That should be interpreted as a software system containing at least these logical components:

```text
┌─────────────────────────────┐
│     RF Environment          │
│  simulated emitter truth    │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│     Receiver Simulator      │
│ frequency + time behaviour  │
└──────────────┬──────────────┘
               │ observations
               ▼
┌─────────────────────────────┐
│ Observation / Feature Layer │
│ hits, misses, history, etc. │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│ ML Decision / Scheduler     │
│ chooses next scan action    │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│ Performance Evaluation      │
│ compare with baseline       │
└─────────────────────────────┘
```

---

# 6. What the simulated RF environment means

This is one of the most important requirements.

The statement asks for a simulated RF environment that contains **truth information** about emitter status for each frequency band at each time slot.

A simple representation is a matrix:

```text
              Time
             t0 t1 t2 t3 t4
Band B1       0  0  1  1  0
Band B2       0  1  1  0  0
Band B3       0  0  0  0  1
Band B4       1  1  0  0  0
```

Where:

- `1` = transmission exists
- `0` = no transmission

This is **ground truth**.

The receiver does not automatically know this complete matrix.

It only gets observations from the bands it actually scans.

That distinction is crucial.

### Recommended simulator

Generate multiple emitter behaviours:

1. **Static emitter**
   - stays in one band.

2. **Intermittent emitter**
   - turns on and off.

3. **Periodic emitter**
   - follows a predictable cycle.

4. **Frequency-agile emitter**
   - changes bands over time.

5. **Spatially scanning emitter abstraction**
   - its detectability/activity changes according to a simulated scanning pattern.

6. **New/unseen emitter**
   - appears after the scheduler has already started learning.

7. **Noise/false-alarm process**
   - receiver occasionally reports activity even when there is no true transmission.

The goal is not photorealistic RF physics. The goal is a controlled environment for evaluating scan decisions.

---

# 7. The receiver model

A useful prototype receiver should have a narrower instantaneous bandwidth than the total spectrum.

For example:

```text
Total simulated spectrum: 100 units
Receiver instantaneous bandwidth: 5 units
```

Therefore it cannot inspect everything simultaneously.

A receiver action might be:

```text
action = choose_band(37)
```

The simulator then returns something like:

```json
{
  "band": 37,
  "time": 128,
  "observed": true,
  "ground_truth": true,
  "detection": true
}
```

The ML system should learn from the observation rather than receiving the entire hidden truth state.

---

# 8. The central ML problem

There are several reasonable formulations.

## Option A — Multi-armed bandit

Each frequency band can initially be treated as an "arm".

The scheduler learns the expected reward of observing each band.

Example:

```text
Band       estimated reward
B1              0.11
B2              0.63
B3              0.08
B4              0.81
B5              0.20
```

The scheduler is then more likely to inspect B4.

### Recommended algorithms

Start with:

- ε-greedy
- UCB
- Thompson Sampling

These are excellent baselines because they are easy to explain.

### Limitation

A standard bandit assumes a relatively stationary reward structure.

Electronic-emitter activity can change over time.

Therefore, a **contextual or restless bandit** formulation is potentially stronger.

---

# 9. Option B — Reinforcement Learning

You can formulate the problem as an RL environment.

### State

A state could include:

```text
recent observation history
+
time since each band was observed
+
recent hit/miss history
+
estimated activity probability
+
recent band transitions
```

### Action

```text
select next frequency band
```

### Reward

A simple reward can combine:

```text
+ positive reward for useful detection
- penalty for missed opportunity
- penalty for excessive scan time
- penalty for false alarms
+ reward for discovering new/important activity
```

Do not make the reward so complicated that nobody can understand it.

A transparent reward function is much easier to defend.

---

# 10. Option C — POMDP / belief-state model

This is a particularly elegant academic interpretation.

The true emitter state is hidden.

The receiver sees only partial observations.

Therefore:

```text
Hidden state
     ↓
Receiver observation
     ↓
Belief update
     ↓
Action selection
     ↓
New observation
```

The scheduler maintains a probability or belief for each band.

Example:

```text
P(active | observations)

B1 = 0.12
B2 = 0.67
B3 = 0.21
B4 = 0.91
```

The scheduler uses these beliefs to select its next action.

This can make the project mathematically strong without requiring a huge neural network.

---

# 11. My recommended approach

Do **not** begin with deep reinforcement learning.

Start with a hierarchy:

### Level 1 — Fixed sweep

```text
B1 → B2 → B3 → ... → BN
```

This is the baseline.

### Level 2 — Random/adaptive heuristic

Choose bands based on recent activity and time since last scan.

### Level 3 — Statistical scheduler

Use:

- Bayesian activity estimates,
- UCB,
- Thompson Sampling.

### Level 4 — Contextual / RL scheduler

Use the richer observation history to learn a policy.

This progression gives you an experimental story:

```text
Fixed baseline
      ↓
Heuristic
      ↓
Bandit
      ↓
ML/RL
```

Even if the final RL model does not outperform everything, the comparison itself is valuable.

---

# 12. The "hits and misses" requirement

The statement explicitly says the model should be trained based on **hits and misses**.

This means the system should record feedback.

Example:

```text
Time  Band  Prediction  Actual  Result
----  ----  ----------  ------  ------
10    B4    active      active  HIT
11    B2    active      idle    MISS
12    B7    idle        active  MISS
13    B4    active      active  HIT
```

Over time, this history should affect future scheduling decisions.

This is the learning loop.

---

# 13. Metrics you are expected to consider

The statement explicitly names several figures of merit.

Do not leave these as words in the report.

Implement them as measurable metrics.

---

## 13.1 Probability of Detection — Pd

A common conceptual definition is:

```text
Pd = correctly detected transmissions
     --------------------------------
     actual transmissions presented
```

Higher is generally better.

---

## 13.2 Probability of False Alarm — Pfa

Conceptually:

```text
Pfa = false detections
      -----------------
      opportunities with no true signal
```

Lower is generally better.

---

## 13.3 Sensitivity

Sensitivity describes how effectively the receiver detects actual events.

In many simplified binary detection settings it is closely related to detection probability.

Be explicit about your exact definition so the judge can reproduce your result.

---

## 13.4 Average Intercept Rate

Measure how frequently the receiver successfully intercepts available transmissions.

You should define the denominator carefully.

For example:

```text
interception rate =
successful intercept events
---------------------------
eligible transmission events
```

---

## 13.5 Average reward / cost function

This is where your scheduling objective becomes measurable.

A possible conceptual objective:

```text
Reward =
  detection benefit
- false alarm cost
- time cost
- missed-opportunity cost
```

Use normalized values so one term does not dominate accidentally.

---

## 13.6 Percentage of correct predictions

If your model predicts whether/where activity will occur:

```text
correct predictions
-------------------
all predictions
```

Again, define the prediction horizon and class treatment.

Accuracy alone is dangerous if transmissions are rare.

Also report precision, recall and F1 where appropriate.

---

## 13.7 Average intercept time error

Measure how far the actual interception time is from a target/predicted/optimal reference time.

For example:

```text
intercept time error =
|actual intercept time - reference time|
```

State exactly what reference you use.

---

# 14. The most important comparison

Your final system must be compared against the open-loop strategy.

At minimum:

```text
Method A: Fixed/open-loop sweep
Method B: Your smart scheduler
```

Use identical:

- RF environment seeds
- emitter behaviours
- total simulation duration
- receiver constraints
- observation budget

Then compare results.

### Example result table

| Metric | Open-loop | Smart scheduler |
|---|---:|---:|
| Probability of detection | 0.61 | 0.79 |
| False alarm probability | 0.08 | 0.06 |
| Interception rate | 0.55 | 0.74 |
| Avg. intercept time | 21.4 | 13.2 |
| Avg. reward | 0.42 | 0.68 |

**Do not fabricate numbers.** These are illustrative only.

---

# 15. Periodic scan receiver requirement

This part is easy to miss.

The statement asks for approaches to **optimally intercept a periodic scan receiver**.

That is a separate analytical problem.

Suppose another emitter follows:

```text
B2 → B5 → B8 → B2 → B5 → B8 → ...
```

If the periodicity can be learned, the scheduler may infer:

```text
period ≈ T
next expected location ≈ B5
```

The system can then test whether exploiting this learned periodic structure improves interception.

### Suggested experiment

Create a periodic emitter with a known hidden period.

Then:

1. Observe it.
2. Estimate its period.
3. Predict its next likely band/time.
4. Schedule observations around the predicted event.
5. Compare with fixed sweeping.

The important academic question is:

> How much performance improvement is possible when temporal structure can be learned?

---

# 16. Frequency-agile emitters

Frequency-agile emitters are harder.

Their band can change:

```text
B2 → B9 → B4 → B12 → B3 → ...
```

A deterministic model may learn the pattern if it is predictable.

A random model should not magically achieve perfect interception.

This is an important realism check.

### Recommended experiment groups

#### Easy

Predictable movement.

#### Medium

Partially predictable movement.

#### Hard

Highly stochastic hopping.

Then show performance as uncertainty increases.

This will make the project substantially more credible.

---

# 17. Suggested architecture

```text
                    ┌───────────────────────┐
                    │ Scenario Generator    │
                    │ emitter behaviours    │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ RF Environment        │
                    │ hidden ground truth   │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Receiver Simulator    │
                    │ bandwidth + noise     │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Observation Store     │
                    │ hits / misses / time  │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Feature / Belief      │
                    │ estimation            │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Smart Scheduler       │
                    │ bandit / RL / hybrid  │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Next scan decision    │
                    └───────────┬───────────┘
                                │
                                └──────► loop
```

---

# 18. Suggested software stack

A practical prototype can be built entirely in software.

## Core

- Python
- NumPy
- Pandas
- SciPy

## Machine learning

Choose based on your formulation:

- scikit-learn for statistical models
- PyTorch for custom neural models
- Stable-Baselines3 if RL is selected

## Simulation

- Python-based discrete-event/time-step simulator
- NumPy for vectorized state transitions

## Visualization

- Matplotlib
- Plotly

## Backend

Optional:

- FastAPI

## Frontend/dashboard

Optional:

- React
- Streamlit
- Plotly Dash

### Recommendation

For an SIH prototype, **do not spend most of your time building a beautiful web application**.

The core scheduler and evaluation engine matter much more.

---

# 19. What the dashboard should show

A good demo dashboard could contain:

### Panel 1 — Spectrum map

```text
Frequency →
Time ↓

B1  ░ ░ █ █ ░ ░
B2  ░ █ █ ░ ░ █
B3  ░ ░ ░ █ ░ ░
...
```

Use colour/intensity to represent simulated activity.

### Panel 2 — Receiver location

Show where the receiver is currently scanning.

### Panel 3 — Scheduler decision

```text
Selected band: B17
Reason/score: 0.83
Estimated activity: 78%
```

### Panel 4 — Performance

Live comparison:

```text
                 Open Loop     Smart
Detection          62%         79%
Intercept rate     55%         74%
Avg time           21s         13s
```

### Panel 5 — Learning curve

Show reward/interception performance over time.

---

# 20. Suggested "killer demo"

A strong five-minute demonstration could be:

### Step 1 — Explain the constraint

> "We have a wide spectrum, but our receiver can inspect only a small portion at a time."

### Step 2 — Run the fixed scanner

Show it sweeping.

### Step 3 — Introduce a new emitter

Make an important emitter appear after the sweep has started.

### Step 4 — Run the smart scheduler

Show the scheduler rapidly increasing attention to the relevant region after observing evidence.

### Step 5 — Compare

Display:

```text
Open-loop:
intercept = late

Smart:
intercept = earlier
```

### Step 6 — Stress test

Change the emitter behaviour.

Show that the system adapts rather than relying on one memorized sequence.

---

# 21. Suggested novelty

Do not claim:

> "We used AI."

That is not sufficient.

Your novelty should be in the **decision-making strategy**.

Possible directions:

## Novelty A — Uncertainty-aware scheduler

Do not only maximize predicted activity.

Balance:

```text
exploitation
+
exploration
```

The system sometimes checks uncertain bands because they may contain previously unseen activity.

---

## Novelty B — Time-aware bandit

Use:

- probability of activity,
- time since last scan,
- recent activity,
- estimated periodicity.

This is more suitable than treating each band as completely independent.

---

## Novelty C — Hierarchical scheduler

First choose a region:

```text
Spectrum
 ↓
Region
 ↓
Band
 ↓
Dwell duration
```

This can reduce the action space.

---

## Novelty D — Hybrid model

Combine:

```text
physics/rules
+
statistical estimation
+
ML scheduler
```

This is often easier to explain and validate than a black-box deep RL model.

---

# 22. Suggested mathematical formulation

Define:

```text
B = {1, 2, ..., N}
```

as the set of frequency bands.

At time `t`, let:

```text
x_t ∈ {0,1}^N
```

represent the true emitter state.

The receiver does not observe all of `x_t`.

It chooses:

```text
a_t ∈ B
```

and receives an observation:

```text
o_t
```

The scheduler maintains an estimated belief:

```text
p_t(i) = P(x_t(i)=1 | observations up to t)
```

The decision can then maximize something like:

```text
a_t = argmax_i Score(i,t)
```

where:

```text
Score(i,t)
=
α · predicted_detection
+ β · uncertainty
+ γ · freshness
+ δ · temporal_pattern
- λ · scan_cost
```

This is a conceptual model, not a mandated formula.

The exact formulation is your research contribution.

---

# 23. Training strategy

Do not train and test on the same emitter scenarios.

Use:

```text
Training scenarios
        ↓
Model learning
        ↓
Validation scenarios
        ↓
Hyperparameter selection
        ↓
Completely unseen test scenarios
```

### Important

Change the random seed.

Change:

- number of emitters
- activity probability
- periodicity
- hopping behaviour
- noise
- appearance time
- receiver conditions

This tests whether the scheduler learned a strategy rather than memorizing your simulator.

---

# 24. Adversarial/generalization testing

This is one of the strongest additions you can make.

Suppose your scheduler performs very well on:

```text
Emitter pattern A
```

but badly on:

```text
Emitter pattern B
```

That tells you the model is overfitting.

Create scenario families:

```text
Scenario A — stationary
Scenario B — intermittent
Scenario C — periodic
Scenario D — frequency agile
Scenario E — mixed
Scenario F — unseen/adversarial
```

Report performance separately.

---

# 25. Dataset

A current third-party SIH problem mirror identifies a dataset/resource associated with the statement as:

**J. C. Wise, Radar Emitter Database, 2024**

It points to a synthetic radar dataset hosted on Hugging Face.

Treat that as a **reference/resource**, not as permission to assume that it exactly represents DRDO's intended operational environment.

The statement itself primarily requires a **simulated RF environment with ground truth**.

### Recommendation

Use the dataset to inspire or seed emitter characteristics, but make your own controlled simulator the primary experimental environment.

This lets you generate ground-truth scenarios with known answers.

---

# 26. What NOT to do

## Don't build only a dashboard

A dashboard without a demonstrably better scheduler is weak.

## Don't use a random neural network just because it is AI

A simple bandit can be more convincing if it produces better results.

## Don't hide the baseline

Your fixed/open-loop comparison is central to the problem.

## Don't use only accuracy

If transmissions are rare, a model that always predicts "no transmission" can achieve misleadingly high accuracy.

## Don't train on one scenario

Your model may simply memorize the simulator.

## Don't claim real-world military performance

Your prototype is a simulation/research demonstrator.

## Don't assume classified hardware parameters

The SIH statement does not require you to reproduce classified DRDO systems.

## Don't ignore periodic emitters

The statement explicitly asks for a strategy for periodic scan receivers.

---

# 27. Minimum viable prototype

If time is limited, build this:

### Simulator

- 20–100 frequency bands
- time-step simulation
- 5–20 emitters
- static/intermittent/periodic/agile modes
- ground truth matrix

### Receiver

- one selected band at a time
- configurable observation duration
- detection probability
- false alarm probability

### Baselines

- fixed sequential sweep
- random selection

### Smart method

- UCB or Thompson Sampling
- plus a simple time-awareness/freshness feature

### Metrics

- Pd
- Pfa
- interception rate
- average intercept time
- average reward

### UI

- spectrum activity map
- current scan position
- performance comparison

This is enough to demonstrate the central idea.

---

# 28. Stronger prototype

For a more competitive submission:

```text
RF simulator
+
receiver model
+
multiple baseline algorithms
+
contextual/restless bandit
+
periodicity estimator
+
uncertainty-aware exploration
+
unseen scenario testing
+
ablation study
+
visual analytics dashboard
```

### Ablation study

Remove components one at a time:

```text
Full model
Full - periodicity
Full - uncertainty
Full - freshness
Full - temporal history
```

Then show what actually contributes to performance.

This is much stronger than saying "our AI is advanced."

---

# 29. Evaluation protocol I recommend

Run at least:

```text
100+ random episodes
```

for each scenario class if computationally practical.

For every episode record:

```text
seed
number of emitters
emitter types
scan budget
detections
false alarms
misses
intercept times
reward
```

Then report:

- mean
- median
- standard deviation
- confidence intervals where possible

Do not show only the best run.

---

# 30. Suggested result visualizations

The best plots are:

### A. Interception rate vs time

Shows how quickly the scheduler discovers useful emitters.

### B. Average intercept time

Compare algorithms.

### C. Pd vs Pfa

Shows detection trade-offs.

### D. Reward curve

Shows learning.

### E. Band-selection heatmap

Shows what the scheduler is actually doing.

### F. Performance vs emitter unpredictability

This is especially valuable for frequency-agile scenarios.

---

# 31. How to explain the project to a non-EW judge

Do not begin with:

> "Electronic Support Measures perform spectrum surveillance..."

Instead say:

> "Imagine a security guard who can look at only one camera at a time, while important events can happen in any camera at any moment. A fixed schedule checks every camera equally. Our system learns which camera is most likely to contain an important event and decides where to look next."

Then map:

```text
Camera → frequency band
Event → RF transmission
Guard's decision → receiver scheduler
Missed event → missed intercept
Learning → ML scheduler
```

This makes the problem understandable in seconds.

---

# 32. What the final software should deliver

A strong final demonstrator should contain:

## 1. RF environment simulator

Generates controlled emitter activity.

## 2. Receiver simulator

Models limited observation capability.

## 3. Baseline scheduler

Implements the conventional open-loop scan.

## 4. Smart scheduler

Uses learned/adaptive decision-making.

## 5. Training engine

Learns from observations/hits/misses.

## 6. Evaluation engine

Computes all major metrics.

## 7. Visualization dashboard

Shows the scheduler operating.

## 8. Experiment manager

Allows repeatable experiments with random seeds.

## 9. Report generator

Exports results.

---

# 33. Suggested project folder structure

```text
sih26055/
│
├── README.md
├── requirements.txt
│
├── config/
│   ├── default.yaml
│   └── scenarios.yaml
│
├── simulator/
│   ├── environment.py
│   ├── emitters.py
│   ├── receiver.py
│   └── noise.py
│
├── schedulers/
│   ├── open_loop.py
│   ├── random.py
│   ├── ucb.py
│   ├── thompson.py
│   └── smart_scheduler.py
│
├── learning/
│   ├── features.py
│   ├── trainer.py
│   └── evaluation.py
│
├── experiments/
│   ├── train.py
│   ├── test.py
│   └── benchmark.py
│
├── metrics/
│   └── metrics.py
│
├── dashboard/
│   └── app.py
│
├── data/
│   ├── generated/
│   └── external/
│
└── results/
    ├── figures/
    └── tables/
```

---

# 34. Suggested team division

For a 4–6 member team:

### Member 1 — Domain + simulation

Own:

- RF abstraction
- emitter models
- receiver model

### Member 2 — ML

Own:

- bandit/RL model
- feature engineering
- training

### Member 3 — Evaluation

Own:

- metrics
- baselines
- experiments
- statistical analysis

### Member 4 — Software

Own:

- backend
- experiment pipeline
- data management

### Member 5 — Visualization

Own:

- dashboard
- spectrum visualization
- demo

### Member 6 — Research/documentation

Own:

- literature review
- mathematical formulation
- report
- presentation
- validation

If your team is smaller, combine roles.

---

# 35. Suggested development sequence

## Phase 1 — Understand

Write down:

```text
What is observed?
What is hidden?
What can the receiver control?
What constitutes success?
```

## Phase 2 — Simulator

Build the environment before the ML model.

## Phase 3 — Baseline

Implement the fixed sweep.

## Phase 4 — Simple adaptive model

Implement UCB/Thompson Sampling.

## Phase 5 — Time awareness

Add:

- time since observation
- temporal activity
- periodicity

## Phase 6 — ML/RL

Only after the baseline works.

## Phase 7 — Evaluation

Run hundreds of controlled experiments.

## Phase 8 — Visualization

Make the result easy to understand.

## Phase 9 — Stress testing

Test unseen emitter behaviour.

## Phase 10 — Presentation

Tell the story:

```text
Fixed scan
   ↓
Problem
   ↓
Learning
   ↓
Smart scheduling
   ↓
Measured improvement
```

---

# 36. Key research questions your team can answer

A good SIH project should produce conclusions, not just software.

Your project could investigate:

1. Does adaptive scheduling reduce average intercept time?
2. How much does it improve interception rate?
3. What is the trade-off between detection and false alarms?
4. Does exploration improve detection of new emitters?
5. How quickly can the scheduler adapt to a new emitter?
6. Does periodicity estimation improve interception?
7. How does performance change as frequency hopping becomes more unpredictable?
8. Does a simple bandit outperform a fixed sweep?
9. Does RL outperform simpler approaches enough to justify its complexity?
10. How robust is the scheduler to noise and false alarms?

These questions can become the backbone of your technical report.

---

# 37. Suggested final architecture

If I were designing the SIH submission, I would use:

```text
                 ┌──────────────────┐
                 │ Scenario Generator│
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │ RF Environment   │
                 │ Ground Truth     │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │ Receiver Model   │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │ Observation      │
                 │ History          │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │ Belief / Feature │
                 │ Estimation       │
                 └────────┬─────────┘
                          ↓
              ┌────────────────────────┐
              │ Adaptive Scheduler     │
              │                        │
              │ UCB / Thompson / RL    │
              └───────────┬────────────┘
                          ↓
                 ┌──────────────────┐
                 │ Next Band/Action │
                 └────────┬─────────┘
                          │
                          └─────── loop
```

with a parallel evaluation pipeline:

```text
Open-loop baseline ─────┐
Random baseline ────────┤
Smart scheduler ────────┤──► Metrics ──► Comparison
RL scheduler (optional) ┘
```

---

# 38. What would make this submission genuinely strong

The strongest version is **not**:

> "We made an AI model that predicts radar signals."

It is:

> "We formulated spectrum interception as a sequential decision problem, built a controlled RF environment with hidden ground truth, reproduced a conventional open-loop scanning strategy, developed an adaptive scheduler that learns from hits and misses, and demonstrated statistically significant improvements in interception time/rate across unseen emitter scenarios while explicitly measuring detection and false-alarm trade-offs."

That is a much more defensible technical contribution.

---

# 39. Potential pitfalls and how to address them

| Risk | Why it matters | Mitigation |
|---|---|---|
| Simulator bias | Model may learn simulator quirks | Multiple scenario families |
| Overfitting | Good training result but poor unseen performance | Separate test seeds/scenarios |
| Rare events | Accuracy can become misleading | Pd/Pfa/precision/recall |
| RL instability | Hard to reproduce | Keep bandit baseline |
| Complex dashboard | Wastes development time | Build UI after core engine |
| Unrealistic claims | Defence domain is sensitive | Clearly label simulation |
| Excessive model complexity | Hard to explain | Compare against simple baselines |
| Ignoring periodicity | Misses explicit PS requirement | Dedicated periodic experiment |
| No baseline | Improvement cannot be demonstrated | Fixed open-loop baseline |
| No statistical testing | One lucky run proves little | Many repeated episodes |

---

# 40. Safety and scope boundary

This project can be implemented as a **simulation and scheduling research system**.

For an SIH prototype, keep the work focused on:

- simulated emitters,
- synthetic RF states,
- receiver abstraction,
- ML scheduling,
- detection statistics,
- optimization,
- visualization.

Do not represent the prototype as a deployable military electronic-warfare system, and do not rely on classified operational parameters.

The technical contribution is the **adaptive decision algorithm and evaluation framework**.

---

# 41. What SIH judges should be able to see

By the end of the demo, the judges should be able to answer "yes" to all of these:

- Does the team understand the scanning problem?
- Is there a working simulated RF environment?
- Is there a conventional/open-loop baseline?
- Does the receiver have limited observation capability?
- Does the ML scheduler actually make decisions?
- Does it learn from hits/misses?
- Is there measurable improvement?
- Are Pd and Pfa measured?
- Is interception time measured?
- Is interception rate measured?
- Is the periodic-emitter case addressed?
- Does the system generalize to unseen scenarios?
- Can the team explain why its algorithm works?

---

# 42. Submission/report checklist

## Problem understanding

- [ ] Problem ID 26055 clearly stated
- [ ] DRDO identified as organization
- [ ] Software track identified
- [ ] Electronic Support context explained
- [ ] Open-loop limitation explained

## Simulation

- [ ] Multi-band spectrum
- [ ] Time dimension
- [ ] Ground truth
- [ ] Multiple emitter behaviours
- [ ] Frequency-agile scenario
- [ ] Periodic scenario
- [ ] Noise/false alarm model

## Scheduler

- [ ] Baseline
- [ ] Adaptive algorithm
- [ ] Hit/miss feedback
- [ ] Exploration/exploitation
- [ ] Time-aware scheduling

## Evaluation

- [ ] Probability of detection
- [ ] Probability of false alarm
- [ ] Sensitivity
- [ ] Interception rate
- [ ] Reward/cost
- [ ] Correct prediction percentage
- [ ] Intercept time error
- [ ] Average intercept time

## Validation

- [ ] Multiple random seeds
- [ ] Unseen scenarios
- [ ] Baseline comparison
- [ ] Stress testing
- [ ] Ablation study

## Demo

- [ ] Live spectrum visualization
- [ ] Receiver position
- [ ] Scheduler decision
- [ ] Hit/miss feedback
- [ ] Metric comparison
- [ ] New emitter demonstration
- [ ] Periodic emitter demonstration

---

# 43. Suggested presentation structure

### Slide 1 — Problem

**Wide spectrum + narrow receiver = scheduling problem**

### Slide 2 — Why fixed scanning fails

Show a simple timeline.

### Slide 3 — Our insight

**The receiver should learn where and when to look.**

### Slide 4 — Architecture

RF environment → receiver → observations → ML scheduler.

### Slide 5 — Algorithm

Explain the decision loop.

### Slide 6 — Baseline

Fixed/open-loop sweep.

### Slide 7 — Results

Show the most important numerical comparison.

### Slide 8 — Stress test

Unseen/frequency-agile/periodic scenarios.

### Slide 9 — Demo

Live scheduler.

### Slide 10 — Impact

Earlier interception + better scan efficiency + adaptive behaviour.

---

# 44. Suggested one-minute pitch

> "Electronic-warfare receivers have to monitor a wide spectrum even though they can observe only a small portion at a time. Conventional open-loop scanning follows a predetermined schedule, which can waste observation time on uninformative bands and delay interception of newly appearing emitters. We model this as a sequential decision problem. Our system creates a simulated RF environment with ground-truth emitter activity, models a constrained receiver, and trains an adaptive scheduler from hits and misses. The scheduler continuously decides which band to inspect next using learned activity, uncertainty and temporal information. We benchmark it against conventional open-loop scanning using probability of detection, false-alarm probability, interception rate, reward and intercept time. We also test periodic and frequency-agile emitters to measure how well the strategy generalizes."

---

# 45. Final interpretation

### In plain English:

**DRDO is asking you to build a smart "where should I look next?" brain for a spectrum-monitoring receiver.**

The receiver cannot watch everything at once.

The environment changes.

Some emitters may be predictable.

Some may appear suddenly.

Some may change frequency.

Your software should learn from what it observes and continuously improve its scan decisions.

The most important thing is therefore **not the dashboard, not the buzzwords, and not the biggest neural network**.

The core is:

```text
SIMULATE
   ↓
OBSERVE
   ↓
LEARN
   ↓
DECIDE
   ↓
SCAN
   ↓
MEASURE
   ↓
LEARN AGAIN
```

---

# 46. Recommended project direction

If the goal is a strong SIH submission rather than merely a working prototype, the recommended path is:

```text
                 START
                   │
                   ▼
        Build RF environment
                   │
                   ▼
        Build receiver model
                   │
                   ▼
       Implement open-loop scan
                   │
                   ▼
       Implement UCB/Thompson
                   │
                   ▼
        Add temporal features
                   │
                   ▼
    Add periodicity + uncertainty
                   │
                   ▼
       Optional RL scheduler
                   │
                   ▼
       Evaluate on unseen data
                   │
                   ▼
       Compare statistically
                   │
                   ▼
      Build visualization/demo
                   │
                   ▼
              SIH PITCH
```

### My strongest recommendation

**Do not make "deep learning" the starting point.**

Make **adaptive scheduling** the starting point.

Then use the simplest model that demonstrably solves the problem. If a bandit/hybrid approach already beats open-loop scanning, that is a strong result. If RL adds measurable improvement, add it as the advanced layer.

---

# 47. Source and verification notes

The core problem description reproduced/interpreted in this document is based on the currently available SIH 2026 problem-statement records for **SIH26055**.

Primary/reference sources consulted:

1. Smart India Hackathon 2026 problem-statement portal/dataset references.
2. SIH26055 mirror containing the full statement, metadata, and expected solution.
3. Independent SIH 2026 problem-statement datasets used to cross-check the ID/title/organization.
4. A SIH-specific problem page identifying the associated synthetic radar-emitter dataset.

### Metadata discrepancy

Current mirrors do not agree on the exact submission deadline:

- one current SIH26055 mirror displays **30 September 2026**;
- another displays **20 September 2026**.

Therefore **do not rely on this document for the final deadline**. Check the live official SIH portal immediately before submission.

The statement itself, however, is consistent across the sources on the central requirements:

- smart scan strategy,
- simulated RF environment,
- truth information,
- two-dimensional frequency/time interception,
- learning from hits and misses,
- machine-learning scheduler,
- minimizing intercept time,
- maintaining high interception rate,
- and addressing periodic scanning behaviour.

---

# 48. Bottom line

**Problem 26055 is fundamentally an AI/optimization problem disguised in Electronic Warfare terminology.**

The abstract problem is:

> **Given limited observation capacity and a changing hidden environment, learn the best sequence of observations to maximize useful detections while minimizing time and false alarms.**

That makes the problem closely related to:

- sequential decision making,
- multi-armed bandits,
- contextual bandits,
- POMDPs,
- reinforcement learning,
- Bayesian inference,
- active sensing,
- scheduling,
- and adaptive search.

That is the conceptual lens through which your team should approach it.
