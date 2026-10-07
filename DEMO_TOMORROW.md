# Review-I Demo Script — Member B

## Before the review

Run:

```bash
python demo/run_selector.py
```

This creates:

```text
demo/selector_output.csv
```

Open these plots:

```text
results/01_queue_vs_time.png
results/02_utilization_vs_time.png
results/03_rtt_vs_time.png
results/05_signal_scores.png
results/06_active_signal_vs_time.png
```

## What to say

### 1. Start with the problem

"Different congestion signals capture different aspects of congestion. Our project studies whether a lightweight runtime mechanism can select among queue, utilization and RTT as network conditions change."

### 2. Show the three candidate inputs

```text
Queue
Utilization
RTT
```

### 3. Show the score equations

```text
QueueScore =
    wq1 × normalized_queue_level
  + wq2 × normalized_queue_growth

UtilScore =
    wu1 × normalized_utilization
  + wu2 × utilization_persistence

RTTScore =
    wr1 × normalized_RTT_growth
  + wr2 × RTT_growth_persistence
```

### 4. Show selection

```text
candidate = argmax(QueueScore, UtilScore, RTTScore)
```

### 5. Explain hysteresis

"A new signal is not selected just because its score is slightly higher. It has to exceed the current signal by a fixed margin and remain stronger for K consecutive samples."

### 6. State the boundary

"This is our Review-I algorithm prototype. The input data included here are synthetic so that we can demonstrate the selector before Ishaan's ns-3 measurements are connected. They are not final network results."

### 7. Explain the next integration

"Ishaan's ns-3 module will produce queue, utilization and RTT measurements. We will feed those measurements into this selector without changing the selector logic."

### 8. Explain the later research experiment

"We will compare RTT-only, Queue-only, Utilization-only, fixed multi-signal, and adaptive selection using the same common experimental rate-control law."

---

# Teacher questions we should be ready for

**Why not use all three all the time?**

"That is why fixed multi-signal is a baseline in our final evaluation."

**Why hysteresis?**

"To reduce unnecessary signal flapping caused by small measurement changes."

**Is this machine learning?**

"No. It is a deterministic lightweight policy based on normalized evidence and hysteresis."

**Are these signals new?**

"No. We are not claiming the signals themselves are new."

**What is the contribution?**

"We are studying the specific runtime active-signal-selection formulation and evaluating it against fixed alternatives under changing network conditions."

**Is this a production TCP algorithm?**

"No. The final study uses a common experimental TCP-like rate-control law to isolate the effect of signal selection."

**Are the current graphs final results?**

"No. They are selector-prototype demonstrations using synthetic data. Final results will use ns-3 measurements."

