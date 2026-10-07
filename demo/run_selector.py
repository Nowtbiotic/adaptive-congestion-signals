
from pathlib import Path
import csv
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from selector import SelectorConfig, run_selector


def main():
    input_path = ROOT / "demo" / "synthetic_review1_input.csv"
    output_path = ROOT / "demo" / "selector_output.csv"
    config_path = ROOT / "config_demo.json"

    cfg_data = json.loads(config_path.read_text(encoding="utf-8"))["selector"]
    cfg = SelectorConfig(**cfg_data)

    with input_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    out = run_selector(rows, cfg)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=out[0].keys())
        writer.writeheader()
        writer.writerows(out)

    switches = [r for r in out if r["switched"]]
    print(f"Processed samples : {len(out)}")
    print(f"Signal switches   : {len(switches)}")
    for row in switches:
        print(
            f"  t={row['time']:.1f}s -> {row['active_signal']} "
            f"(Queue={row['QueueScore']:.3f}, "
            f"Util={row['UtilScore']:.3f}, "
            f"RTT={row['RTTScore']:.3f})"
        )
    print(f"Output            : {output_path}")


if __name__ == "__main__":
    main()
