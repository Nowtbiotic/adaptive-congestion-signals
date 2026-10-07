# Review-I Algorithm / Research Deliverable — Your Part

## Project

**Runtime Selection of In-Network Congestion Signals for TCP Under Dynamic Network Conditions**

### Your role

**Member B — Algorithm / Research**

### Important boundary

This folder is the **Review-I prototype for the algorithm/research side**.

It does **not** contain Ishaan's ns-3 implementation and does **not** pretend that the synthetic demonstration data are real ns-3 results.

The prototype is designed so that Ishaan's later CSV can replace the synthetic input without changing the core selector.

---

# 1. What you need to explain tomorrow

The project has three candidate congestion signals:

1. Queue occupancy / queue growth
2. Link utilization / utilization persistence
3. RTT growth / RTT-growth persistence

The selection pipeline is:

```text
Queue + Utilization + RTT
              |
              v
        Normalization
              |
              v
   QueueScore / UtilScore / RTTScore
              |
              v
            argmax
              |
              v
       Candidate signal
              |
              v
          Hysteresis
              |
              v
        Active signal
```

The active signal will later feed the **common experimental TCP-like rate-control law**.

---

# 2. Exact score formulation

```text
QueueScore =
    wq1 × normalized_queue_level
  + wq2 × normalized_queue_growth
```

```text
UtilScore =
    wu1 × normalized_utilization
  + wu2 × utilization_persistence
```

```text
RTTScore =
    wr1 × normalized_RTT_growth
  + wr2 × RTT_growth_persistence
```

Then:

```text
candidate_signal = argmax(
    QueueScore,
    UtilScore,
    RTTScore
)
```

The selected signal is the one with the strongest congestion evidence **under the predefined policy**. It is not claimed to be the objectively best signal.

---

# 3. Normalization

The prototype uses:

```text
normalized_value =
    clamp((x - lower_bound) /
          (upper_bound - lower_bound), 0, 1)
```

All evidence values therefore lie in `[0, 1]`.

The final project must freeze normalization bounds and selector parameters **before the final evaluation**.

---

# 4. Prototype definitions

The current code calculates:

### Queue level

Queue occupancy is normalized against a configured queue range.

### Queue growth

Positive queue change is converted to a rate:

```text
(queue_current - queue_previous) / Δt
```

and normalized.

### Utilization

Bottleneck utilization is normalized from `[0, 1]`.

### Utilization persistence

For the prototype, persistence is the fraction of recent samples whose utilization is above the configured persistence threshold.

### RTT growth

Positive RTT change is converted to:

```text
(RTT_current - RTT_previous) / Δt
```

and normalized.

### RTT-growth persistence

For the prototype, persistence is the fraction of recent samples whose positive RTT growth is above the configured persistence threshold.

These are implementation definitions for the prototype. They are not claims that the project has proven one universally correct way to define persistence.

---

# 5. Hysteresis

The selector does not switch immediately whenever another score is slightly higher.

The switching condition is:

```text
new_score > current_score + H
```

and the condition must persist for:

```text
K consecutive samples
```

Then:

```text
switch signal
```

Otherwise:

```text
keep current signal
```

This is intended to reduce signal flapping caused by small measurement fluctuations.

---

# 6. Prototype parameter values

The prototype uses:

```text
All score weights = 0.5 / 0.5

H = 0.08

K = 3 samples

History = 5 samples
```

These are **Review-I demonstration defaults**, not final research results.

The final evaluation parameters must be frozen before running the main comparison experiments.

---

# 7. Synthetic 40-second demonstration

The included input follows the project's intended dynamic pattern:

```text
0–10 s
low load

10–20 s
competing load / queue buildup

20–30 s
heavy offered load / high utilization

30–40 s
recovery
```

The included data are **synthetic prototype data**.

They are only used to demonstrate that the selector implementation works before Ishaan's real ns-3 measurements are available.

Do not present these values as measured network results.

---

# 8. What the prototype demonstrates

It demonstrates that:

1. heterogeneous measurements can be normalized;
2. the three signal evidence scores can be calculated;
3. a candidate signal can be selected by `argmax`;
4. hysteresis can prevent immediate switching;
5. the active signal and switching events can be logged;
6. the selector is independent from the ns-3 measurement source.

---

# 9. Files

```text
src/selector.py
    Core Signal Selection Policy.

config_demo.json
    Prototype parameter configuration.

demo/synthetic_review1_input.csv
    Synthetic Review-I input data.

demo/selector_output.csv
    Selector output and scores.

results/
    Preliminary prototype graphs.
```

---

# 10. Running the prototype

From this folder:

```bash
python demo/run_selector.py
```

Or import the policy directly:

```python
from src.selector import SelectorConfig, SignalSelectionPolicy
```

Then supply rows containing:

```text
time
queue
utilization
rtt_ms
```

---

# 11. Later integration with Ishaan

Ishaan's ns-3 side should eventually provide a CSV with at least:

```text
time
queue
utilization
rtt_ms
```

Your selector can then use the real measurements.

The future pipeline is:

```text
Ishaan's ns-3
      |
      v
queue / utilization / RTT CSV
      |
      v
YOUR selector
      |
      v
selected signal
      |
      v
common rate controller
```

This keeps the two pieces modular.

---

# 12. What comes after Review-I

Do not implement these for tomorrow unless time is left after the required work:

- common rate controller integration;
- RTT-only baseline;
- Queue-only baseline;
- Utilization-only baseline;
- fixed multi-signal baseline;
- full adaptive network control;
- hysteresis ablation;
- RTT contribution ablation;
- repeated final experiments;
- final dashboard.

Those belong to later phases of the project.

---

# 13. Teacher explanation

### Problem

Different network-side congestion signals provide different types of information, and their usefulness can vary as network conditions change.

### Proposed idea

Use a lightweight runtime Signal Selection Policy to choose among queue, utilization, and RTT.

### How?

```text
measure
  ↓
normalize
  ↓
score
  ↓
choose candidate
  ↓
apply hysteresis
  ↓
select active signal
```

### What happens after selection?

The selected signal will eventually be passed to one common experimental rate-control law.

### Why a common controller?

To isolate the question of **signal selection** rather than comparing completely different congestion-control algorithms.

### What will be compared later?

```text
RTT-only
Queue-only
Utilization-only
Fixed multi-signal
Adaptive selection
```

### Novelty wording

Use:

> "To the best of our literature search, we did not identify a prior study matching the exact runtime signal-selection policy and experimental formulation implemented in this work."

Do not claim absolute novelty.

---

# 14. Likely teacher questions

## Why not just use all three signals?

That is why the project includes a **fixed multi-signal baseline**.

We want to compare:

```text
fixed single signal
vs
fixed multi-signal
vs
runtime selection
```

## Why is hysteresis needed?

Without hysteresis, small fluctuations can cause repeated signal switching.

## Are you using machine learning?

No. The selector is a deterministic, lightweight policy using predefined normalized evidence scores and hysteresis.

## Is this a new TCP standard?

No. The rate controller is a common experimental TCP-like control law for the study.

## Are queue, utilization, and RTT new signals?

No. The research does not claim that.

## What is your specific contribution?

The study investigates the specific runtime active-signal-selection formulation under dynamically changing network conditions and compares it against fixed alternatives.

## Is tomorrow's synthetic data your final result?

No. Tomorrow's prototype data only demonstrate the selector implementation. Final performance results will come from the ns-3 experiments.

---

# 15. One sentence to remember

> **I am implementing the policy that decides which of the three congestion signals should currently be active; Ishaan is building the ns-3 network that produces those signals.**

