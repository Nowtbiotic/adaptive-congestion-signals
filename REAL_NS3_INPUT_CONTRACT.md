# Real ns-3 Integration Contract

When Ishaan finishes the Review-I ns-3 measurement side, provide a CSV with these columns:

```text
time,queue,utilization,rtt_ms
```

Example:

```text
0.1,5,0.62,25.4
0.2,7,0.65,25.9
0.3,12,0.71,27.1
```

The selector does not require the simulator to be built into the same program.

The intended interface is:

```text
ns-3
  ↓
CSV
  ↓
SignalSelectionPolicy
  ↓
selector_output.csv
```

## Important

- `queue` is expected in packets.
- `utilization` is expected as a fraction in `[0,1]`.
- `rtt_ms` is expected in milliseconds.
- `time` must be strictly increasing.
- The normalization bounds must be reviewed before final evaluation.
- Final selector weights and hysteresis parameters must be frozen before final evaluation.
- Do not use synthetic demo data as final project results.
