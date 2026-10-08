from __future__ import annotations

import csv
from pathlib import Path
from collections import defaultdict


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "ns3" / "results"

QUEUE_FILE = RESULTS / "queue.csv"
UTIL_FILE = RESULTS / "utilization.csv"
RTT_FILE = RESULTS / "rtt.csv"
OUTPUT_FILE = RESULTS / "selector_input.csv"


def read_csv(path: Path):
    with path.open("r", newline="") as f:
        return list(csv.DictReader(f))


def main():
    queue_rows = read_csv(QUEUE_FILE)
    util_rows = read_csv(UTIL_FILE)
    rtt_rows = read_csv(RTT_FILE)

    # Use utilization timestamps as the common 100 ms timeline.
    timeline = [float(row["time"]) for row in util_rows]

    # Aggregate queue events into each 100 ms interval.
    queue_by_bin = defaultdict(list)

    for row in queue_rows:
        t = float(row["time"])
        q = float(row["queue_packets"])

        # Find the utilization interval containing this event.
        index = int(round((t - timeline[0]) / 0.1))

        if 0 <= index < len(timeline):
            queue_by_bin[index].append(q)

    # Aggregate RTT events by time bin and average across both nodes.
    rtt_by_bin = defaultdict(list)

    for row in rtt_rows:
        t = float(row["time"])
        rtt = float(row["rtt_ms"])

        index = int(round((t - timeline[0]) / 0.1))

        if 0 <= index < len(timeline):
            rtt_by_bin[index].append(rtt)

    with OUTPUT_FILE.open("w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow([
            "time",
            "queue",
            "utilization",
            "rtt_ms",
        ])

        rows_written = 0

        for index, util_row in enumerate(util_rows):
            time = float(util_row["time"])
            utilization = float(util_row["utilization"])

            queue_values = queue_by_bin.get(index, [])
            rtt_values = rtt_by_bin.get(index, [])

            # Skip bins without the required congestion measurements.
            if not queue_values or not rtt_values:
                continue

            mean_queue = sum(queue_values) / len(queue_values)
            mean_rtt = sum(rtt_values) / len(rtt_values)

            writer.writerow([
                f"{time:.5f}",
                f"{mean_queue:.6f}",
                f"{utilization:.6f}",
                f"{mean_rtt:.6f}",
            ])

            rows_written += 1

    print("Selector input created successfully.")
    print(f"Output : {OUTPUT_FILE}")
    print(f"Rows   : {rows_written}")


if __name__ == "__main__":
    main()