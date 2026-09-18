# Architecture & Requirements Document (ARD)
## POMDP / Belief-State Smart Scan Scheduler
### SIH Problem ID 26055 — Smart Scan Strategy for Electronic Warfare

**Version:** 1.0  
**Status:** Proposed Architecture  
**Domain:** Electronic Support / Adaptive Spectrum Surveillance  
**Primary Approach:** Partially Observable Markov Decision Process (POMDP) with Belief-State Scheduling  
**Implementation Type:** Simulation + Machine Learning / Sequential Decision System

---

# 1. Executive Summary

The objective of this system is to develop an intelligent receiver scheduler capable of deciding **which frequency band to scan and when to scan it** in a dynamic and partially observable RF environment.

Unlike a conventional open-loop receiver that follows a predetermined frequency scan sequence, the proposed system continuously updates its understanding of the environment from receiver observations and uses that information to select the next scan action.

The system models the problem as a **Partially Observable Markov Decision Process (POMDP)**.

The actual state of the RF environment is hidden. The receiver can only observe a limited portion of the spectrum at any given time. Consequently, the scheduler maintains a **belief state** representing its current probability distribution over possible emitter states.

The overall loop is:

```text
Hidden RF Environment
        ↓
   Receiver Action
        ↓
     Observation
        ↓
   Belief Update
        ↓
 Decision / Policy
        ↓
 Next Scan Action
        ↓
       LOOP
```

The system will be evaluated against an open-loop scanning strategy using:

- Probability of Detection (Pd)
- Probability of False Alarm (Pfa)
- Sensitivity
- Interception Rate
- Average Intercept Time
- Intercept Time Error
- Average Reward / Cost
- Prediction performance

The primary design objective is:

> **Minimize interception time while maintaining a high interception rate under limited receiver observation capability.**

---

# 2. Problem Definition

## 2.1 Problem

A receiver must monitor a wide RF spectrum while possessing limited instantaneous observation bandwidth.

At time `t`, multiple emitters may exist in the environment.

An emitter may:

- remain at one frequency,
- turn ON/OFF,
- follow a periodic pattern,
- move between frequencies,
- behave unpredictably,
- appear or disappear over time.

The receiver cannot observe the entire spectrum simultaneously.

Therefore, it must decide:

> **What should I scan next?**

The decision must depend on previous observations.

---

# 3. Why POMDP?

A conventional Markov Decision Process assumes that the current environment state is directly available to the agent.

That assumption is not appropriate here.

The scheduler does **not** know:

```text
Which emitters are active?
Where exactly are they?
When will they transmit?
What will they do next?
```

It only receives observations from the portions of the spectrum that it scans.

Therefore:

```text
True State ≠ Directly Observable
```

This makes the problem naturally suited to a POMDP.

---

# 4. POMDP Definition

A POMDP is represented by:

```text
M = (S, A, O, T, Z, R, γ)
```

where:

| Symbol | Meaning |
|---|---|
| `S` | Hidden environment states |
| `A` | Receiver actions |
| `O` | Receiver observations |
| `T` | State transition model |
| `Z` | Observation model |
| `R` | Reward function |
| `γ` | Discount factor |

The scheduler does not directly know `s ∈ S`.

Instead, it maintains:

```text
b(s) = P(s | observation history)
```

where `b(s)` is the **belief state**.

---

# 5. High-Level Architecture

```text
┌─────────────────────────────────────────────┐
│              RF ENVIRONMENT                 │
│                                             │
│  Emitters / Signals / Noise / Time Dynamics │
└──────────────────────┬──────────────────────┘
                       │
                       │ Hidden State
                       ▼
┌─────────────────────────────────────────────┐
│             RECEIVER SIMULATOR              │
│                                             │
│  Bandwidth Constraint                       │
│  Detection Probability                      │
│  False Alarm Probability                    │
│  Dwell Time                                 │
└──────────────────────┬──────────────────────┘
                       │
                       │ Observation
                       ▼
┌─────────────────────────────────────────────┐
│            OBSERVATION PROCESSOR             │
│                                             │
│  Hit / Miss                                 │
│  Signal features                            │
│  Timestamp                                  │
│  Band                                        │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│              BELIEF ENGINE                   │
│                                             │
│  Prior belief                               │
│  Transition prediction                      │
│  Observation update                         │
│  Uncertainty estimation                     │
└──────────────────────┬──────────────────────┘
                       │
                       │ Belief State
                       ▼
┌─────────────────────────────────────────────┐
│            POLICY / SCHEDULER               │
│                                             │
│  Action evaluation                          │
│  Exploration vs exploitation                │
│  Frequency selection                        │
│  Dwell-time selection                       │
└──────────────────────┬──────────────────────┘
                       │
                       │ Action
                       ▼
                 NEXT SCAN
                       │
                       └───────────────► LOOP
```

---

# 6. System Components

## 6.1 RF Environment Simulator

### Responsibility

Generate the hidden RF world.

### Inputs

- Number of frequency bands
- Number of emitters
- Simulation duration
- Emitter types
- Activity probabilities
- Periodicity
- Frequency-hopping behaviour
- Noise parameters

### Outputs

Hidden ground truth:

```text
state[t][band]
```

Example:

```text
        B1 B2 B3 B4 B5 B6
t0      0  1  0  0  1  0
t1      0  1  0  0  0  0
t2      0  0  0  1  0  0
```

### Requirement

The environment **must maintain ground truth separately from the receiver's observations**.

The scheduler must never receive the complete truth matrix during inference.

### Recommendation

Implement multiple scenario generators rather than one fixed environment.

---

# 7. Emitter Model

Each simulated emitter should have:

```text
Emitter
├── emitter_id
├── current_band
├── activity_state
├── start_time
├── stop_time
├── behaviour_type
├── transition_model
└── optional signal parameters
```

Recommended emitter classes:

### E1 — Static

```text
B4 → B4 → B4 → B4
```

### E2 — Intermittent

```text
ON → OFF → OFF → ON → OFF
```

### E3 — Periodic

```text
B2 → B5 → B2 → B5 → B2
```

### E4 — Frequency Agile

```text
B2 → B9 → B4 → B7 → B1
```

### E5 — Random

Band/activity changes according to a stochastic model.

### E6 — Previously unseen emitter

Appears after the scheduler has already learned the environment.

---

# 8. Receiver Model

The receiver represents the sensing limitations.

## 8.1 Required parameters

```text
total_band_count
instantaneous_bandwidth
dwell_time
detection_probability
false_alarm_probability
switching_time
```

Example:

```text
Total bands = 100
Observable bands per action = 1
Dwell time = 1 time unit
Pd = 0.90
Pfa = 0.05
```

These numbers are **simulation parameters**, not claims about real operational systems.

---

# 9. Action Space

The simplest action space is:

```text
A = {scan_band_1, scan_band_2, ..., scan_band_N}
```

The scheduler selects:

```text
a_t = band_i
```

at every decision step.

---

# 10. Extended Action Space

A stronger architecture may allow:

```text
a_t = (frequency_band, dwell_time)
```

For example:

```text
(17, 1)
(42, 2)
(63, 0.5)
```

This allows the scheduler to decide not only **where** to look but also **how long** to look.

### Recommendation

Do not implement this in Version 1.

Start with:

```text
Action = Frequency Band
```

Then add dwell-time optimization once the core POMDP works.

---

# 11. Observation Space

The observation received after scanning a band can contain:

```text
o_t = {
    band_id,
    timestamp,
    detection,
    signal_strength,
    confidence,
    optional_features
}
```

At minimum:

```text
detection ∈ {0,1}
```

Example:

```json
{
  "band": 42,
  "time": 137,
  "detection": 1
}
```

The ground truth must remain hidden.

---

# 12. Observation Model

The observation model is:

```text
P(o | s, a)
```

It describes the probability of obtaining observation `o` when the environment is in state `s` and the receiver takes action `a`.

For a simplified binary detector:

```text
If emitter exists:

P(detection = 1) = Pd

If emitter does not exist:

P(detection = 1) = Pfa
```

Therefore:

```text
                     Emitter present
                           │
              ┌────────────┴────────────┐
              │                         │
           detect                     miss
              │                         │
             Pd                       1-Pd


                    No emitter
                           │
              ┌────────────┴────────────┐
              │                         │
        false alarm                 correct negative
              │                         │
            Pfa                      1-Pfa
```

---

# 13. Belief State

The belief state is the most important component of this architecture.

For every band `i`, maintain:

```text
p_i(t) = probability that band i is currently relevant/active
```

Example:

```text
Band       Belief
B1         0.08
B2         0.71
B3         0.13
B4         0.92
B5         0.44
```

The scheduler can therefore interpret:

```text
B4 is highly likely to contain activity.
B5 is uncertain.
B1 currently appears uninteresting.
```

---

# 14. Initial Belief

At startup there is little information.

The simplest initialization is uniform:

```text
p_i = 1/N
```

for all bands.

For 10 bands:

```text
B1 = 0.10
B2 = 0.10
...
B10 = 0.10
```

A more realistic system can use prior information.

However, for evaluating learning capability:

### Recommendation

Start with an **uninformative or weak prior**.

This demonstrates that the scheduler actually learns.

---

# 15. Belief Update

After taking action `a_t` and receiving observation `o_t`, update the belief.

Conceptually:

```text
Old belief
    ↓
Transition prediction
    ↓
Observation likelihood
    ↓
Bayesian update
    ↓
New belief
```

The general Bayesian update is:

```text
b'(s')
∝
P(o | s', a)
Σ_s P(s' | s, a)b(s)
```

or equivalently:

```text
new belief
=
normalized(
    observation likelihood
    × predicted belief
)
```

---

# 16. Practical Binary Belief Model

For a first implementation, do not maintain an enormous probability distribution over every possible combination of emitters.

That becomes:

```text
2^N
```

possible states for `N` binary bands.

Instead, use a factorized belief:

```text
B = [p1, p2, ..., pN]
```

where each:

```text
pi = P(band i active)
```

is maintained independently or approximately independently.

### This is a major engineering simplification.

---

# 17. Belief Prediction

Between observations, beliefs should evolve.

For a simple persistence model:

```text
p_i(t+1)
=
p_i(t) · persistence
+
(1-p_i(t)) · activation_probability
```

This means an active emitter has some probability of remaining active.

The exact transition model depends on the emitter class.

---

# 18. Periodic Emitter Belief

For periodic emitters, maintain temporal information:

```text
estimated_period
estimated_phase
confidence
```

Example:

```text
Period ≈ 10 time units
Phase ≈ 4
Confidence ≈ 0.82
```

The scheduler can then increase belief around predicted future activity.

---

# 19. Frequency-Agile Belief

For a frequency-agile emitter, use a transition matrix:

```text
        Next band
        B1   B2   B3
B1      .7   .2   .1
B2      .1   .8   .1
B3      .2   .2   .6
```

This represents:

```text
P(next_band | current_band)
```

The scheduler can learn this transition structure from observations.

---

# 20. Policy

The policy determines the next action:

```text
π(a | b)
```

where:

- `b` = current belief state
- `a` = candidate scan action

The simplest deterministic policy:

```text
choose band with highest belief
```

would be:

```python
action = argmax(belief)
```

But this is not sufficient.

Why?

Because it can repeatedly exploit known bands and completely ignore uncertain bands.

---

# 21. Exploration vs Exploitation

The scheduler needs to balance:

### Exploitation

> Scan bands currently believed to contain activity.

### Exploration

> Scan uncertain/unseen bands to discover new activity.

A useful conceptual score is:

```text
Score(i)
=
Expected Detection
+
Exploration Value
+
Temporal Value
-
Scan Cost
```

---

# 22. Recommended Policy

For Version 1:

```text
Score(i)
=
α · p_i
+
β · uncertainty_i
+
γ · freshness_i
+
δ · periodicity_i
```

where:

```text
uncertainty_i = p_i(1-p_i)
```

and:

```text
freshness_i =
time_since_last_observation
```

The scheduler chooses:

```text
argmax Score(i)
```

This gives you a transparent and explainable policy.

---

# 23. Optional POMDP Solver

A full POMDP solver can theoretically optimize:

```text
π*(b)
```

over the belief space.

Possible methods include:

- Point-based value iteration
- POMCP
- Monte Carlo Tree Search
- Approximate dynamic programming

### Recommendation

Do not start here.

The full belief-state space can become extremely large.

Use an approximate belief-state policy first.

Then compare it with a more advanced solver if time permits.

---

# 24. Reward Function

The reward function should represent the actual objective.

A proposed formulation:

```text
R_t =
+ D · detection
- F · false_alarm
- M · missed_opportunity
- C · scan_cost
```

where:

- `D` = detection reward
- `F` = false-alarm penalty
- `M` = missed-event penalty
- `C` = scan cost

---

# 25. Recommended Reward Design

A practical initial reward:

```text
True detection        +10
False alarm            -2
Missed eligible event  -5
Normal empty scan       0
```

These numbers are tunable simulation parameters.

Do not present them as universally correct.

### Important

Run a sensitivity analysis over reward weights.

Otherwise, your results may depend entirely on arbitrary reward choices.

---

# 26. Objective Function

The scheduler should maximize expected cumulative reward:

```text
G_t =
Σ(k=0 → T)
γ^k R_(t+k)
```

where:

```text
γ ∈ [0,1]
```

is the discount factor.

For finite-horizon simulation, you can also use:

```text
G = Σ R_t
```

without discounting.

---

# 27. Primary Optimization Objective

The primary objective should remain aligned with SIH 26055:

```text
Minimize:
    Average Intercept Time

Subject to:
    High Interception Rate
    Acceptable Pfa
```

This is important.

Do not allow the scheduler to maximize reward in a way that produces excellent mathematical reward but poor actual interception performance.

---

# 28. Multi-Objective Formulation

A useful normalized objective is:

```text
J =
w1 · DetectionScore
+
w2 · InterceptionRate
-
w3 · InterceptTime
-
w4 · FalseAlarmRate
```

with:

```text
w1 + w2 + w3 + w4 = 1
```

The exact weights should be experimentally justified.

---

# 29. State Representation

For the factorized belief architecture:

```text
state_t =
[
  p_1,
  p_2,
  ...,
  p_N,

  age_1,
  age_2,
  ...,
  age_N,

  recent_hit_1,
  ...,
  recent_hit_N,

  periodicity_features,
  current_time
]
```

where:

```text
p_i = estimated activity probability
age_i = time since last observation
recent_hit_i = recent observation result
```

---

# 30. Recommended Feature Groups

## Group A — Activity belief

```text
p_i
```

## Group B — Uncertainty

```text
p_i(1-p_i)
```

## Group C — Observation freshness

```text
time_since_last_scan
```

## Group D — Historical activity

```text
hit_rate
miss_rate
recent_activity
```

## Group E — Temporal behaviour

```text
estimated_period
phase
time_to_expected_activity
```

## Group F — Transition behaviour

```text
P(next_band | current_band)
```

---

# 31. Scheduler Decision Pipeline

At every time step:

```text
1. Receive previous observation
2. Update belief
3. Predict future state
4. Calculate uncertainty
5. Calculate temporal predictions
6. Generate candidate actions
7. Score candidate actions
8. Select action
9. Scan selected band
10. Receive observation
11. Record hit/miss
12. Repeat
```

---

# 32. Pseudocode

```python
initialize_environment()

belief = initialize_belief()
history = initialize_history()

for t in range(T):

    predicted_belief = predict_state(
        belief,
        transition_model
    )

    candidate_actions = get_candidate_bands()

    scores = {}

    for band in candidate_actions:

        scores[band] = evaluate_action(
            band=band,
            belief=predicted_belief,
            history=history,
            time=t
        )

    action = select_action(scores)

    observation = receiver.scan(action)

    belief = update_belief(
        belief=predicted_belief,
        action=action,
        observation=observation
    )

    history.record(
        time=t,
        action=action,
        observation=observation
    )

    metrics.update(
        observation=observation,
        ground_truth=environment.truth
    )
```

---

# 33. Software Architecture

Recommended modules:

```text
src/
│
├── environment/
│   ├── rf_environment.py
│   ├── emitter.py
│   ├── scenarios.py
│   └── transitions.py
│
├── receiver/
│   ├── receiver.py
│   ├── detector.py
│   └── noise.py
│
├── belief/
│   ├── belief_state.py
│   ├── updater.py
│   ├── predictor.py
│   └── periodicity.py
│
├── policy/
│   ├── policy.py
│   ├── greedy.py
│   ├── ucb.py
│   └── pomdp_policy.py
│
├── reward/
│   └── reward.py
│
├── metrics/
│   └── metrics.py
│
├── experiments/
│   ├── train.py
│   ├── evaluate.py
│   └── benchmark.py
│
└── dashboard/
    └── app.py
```

---

# 34. Data Flow

```text
Scenario Generator
       │
       ▼
Environment
       │
       ├──────► Ground Truth
       │
       ▼
Receiver
       │
       ▼
Observation
       │
       ▼
Observation History
       │
       ▼
Belief Update
       │
       ▼
Belief State
       │
       ▼
Policy
       │
       ▼
Selected Band
       │
       └──────────► Receiver
```

---

# 35. Functional Requirements

## FR-01 — Environment Generation

The system shall generate RF scenarios containing multiple emitters.

### Acceptance criterion

The simulator can generate repeatable scenarios from a random seed.

---

## FR-02 — Ground Truth

The system shall maintain the true emitter state independently of the receiver.

### Acceptance criterion

The evaluator can access ground truth, while the scheduler cannot.

---

## FR-03 — Receiver Constraint

The system shall enforce limited instantaneous observation bandwidth.

### Acceptance criterion

A receiver cannot inspect unavailable bands during a single action.

---

## FR-04 — Observation Generation

The receiver shall generate observations using configurable Pd and Pfa.

### Acceptance criterion

Measured detection statistics approximately converge toward configured values over sufficiently many trials.

---

## FR-05 — Belief Initialization

The scheduler shall initialize a belief state.

### Acceptance criterion

Every frequency band has a valid probability estimate.

---

## FR-06 — Belief Update

The scheduler shall update its belief after every observation.

### Acceptance criterion

A detection increases the corresponding belief under the configured observation model; a reliable negative observation decreases it.

---

## FR-07 — State Prediction

The scheduler shall propagate beliefs through the transition model.

### Acceptance criterion

Beliefs change even for temporarily unobserved bands when the transition model predicts activity changes.

---

## FR-08 — Action Selection

The scheduler shall select the next scan action from the available action set.

### Acceptance criterion

Every action is valid under receiver constraints.

---

## FR-09 — Learning from Hits/Misses

The scheduler shall incorporate historical observations.

### Acceptance criterion

Two identical current observations can produce different decisions when their historical context differs.

---

## FR-10 — Periodic Behaviour

The system shall support periodic emitter scenarios.

### Acceptance criterion

The scheduler can estimate or exploit periodic activity.

---

## FR-11 — Frequency-Aglile Behaviour

The system shall support emitters whose active band changes over time.

### Acceptance criterion

The scheduler can update beliefs across bands based on learned transitions.

---

## FR-12 — Baseline

The system shall implement a conventional open-loop scan.

### Acceptance criterion

The same scenario can be evaluated using both baseline and smart schedulers.

---

## FR-13 — Metrics

The system shall calculate:

- Pd
- Pfa
- Sensitivity
- Interception rate
- Average intercept time
- Intercept time error
- Reward
- Prediction performance

---

## FR-14 — Reproducibility

Every experiment shall support deterministic random seeds.

### Acceptance criterion

The same seed and configuration reproduce the same simulation.

---

# 36. Non-Functional Requirements

## NFR-01 — Explainability

The scheduler should expose why it selected a band.

Example:

```text
Selected B42

Activity belief:        0.81
Uncertainty:            0.15
Freshness:              0.62
Periodicity score:      0.77
Final score:            0.79
```

---

## NFR-02 — Reproducibility

Experiments must be reproducible.

---

## NFR-03 — Modularity

Environment, receiver, belief model and policy must be independently replaceable.

---

## NFR-04 — Scalability

The system should support increasing:

```text
number of bands
number of emitters
simulation duration
```

without redesigning the architecture.

---

## NFR-05 — Testability

Every major module should have unit tests.

---

## NFR-06 — Performance

The scheduler should make decisions fast enough for real-time simulation.

The prototype does not need to claim real-time operational performance.

---

# 37. Baseline Requirements

The following schedulers should be implemented.

## Baseline 1 — Sequential Sweep

```text
B1 → B2 → B3 → ... → BN
```

## Baseline 2 — Random

```text
random(B1...BN)
```

## Baseline 3 — Greedy Belief

```text
argmax(p_i)
```

These establish increasing levels of intelligence.

---

# 38. Proposed Scheduler Levels

## Level 0

Open-loop.

## Level 1

Greedy belief-state.

## Level 2

Belief + uncertainty.

## Level 3

Belief + uncertainty + freshness.

## Level 4

Belief + temporal/periodicity model.

## Level 5

Full POMDP-inspired scheduler.

This progression provides a powerful ablation study.

---

# 39. Evaluation Matrix

Every algorithm should be tested against the same scenarios.

| Scenario | Open