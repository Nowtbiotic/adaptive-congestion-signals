
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, Optional


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def normalize(value: float, lower: float, upper: float) -> float:
    """Min-max normalization to [0, 1] with clamping."""
    if upper <= lower:
        raise ValueError("Normalization upper bound must be greater than lower bound.")
    return clamp01((value - lower) / (upper - lower))


@dataclass(frozen=True)
class SelectorConfig:
    # Demo defaults only. Freeze final values before the final evaluation.
    queue_min_packets: float = 0.0
    queue_max_packets: float = 100.0
    queue_growth_max_packets_per_sec: float = 100.0

    utilization_min: float = 0.0
    utilization_max: float = 1.0
    utilization_persistence_threshold: float = 0.70

    rtt_growth_min_ms_per_sec: float = 0.0
    rtt_growth_max_ms_per_sec: float = 100.0
    rtt_growth_persistence_threshold_ms_per_sec: float = 0.50

    # Equal prototype weights; final weights must be frozen before final evaluation.
    wq1: float = 0.50
    wq2: float = 0.50
    wu1: float = 0.50
    wu2: float = 0.50
    wr1: float = 0.50
    wr2: float = 0.50

    hysteresis_margin: float = 0.08
    persistence_samples: int = 3
    history_samples: int = 5
    initial_signal: str = "QUEUE"


class SignalSelectionPolicy:
    """
    Lightweight runtime signal-selection policy.

    Input:
        queue occupancy (packets)
        link utilization (0..1)
        RTT (ms)

    Output:
        normalized evidence scores + current active signal.

    This is the algorithm/research prototype. It does not implement
    the common rate controller and does not claim production TCP behavior.
    """

    SIGNALS = ("QUEUE", "UTILIZATION", "RTT")

    def __init__(self, config: SelectorConfig):
        if config.persistence_samples < 1:
            raise ValueError("persistence_samples must be >= 1")
        if config.history_samples < 1:
            raise ValueError("history_samples must be >= 1")
        if config.initial_signal not in self.SIGNALS:
            raise ValueError(f"Unknown initial signal: {config.initial_signal}")

        self.cfg = config
        self.current_signal = config.initial_signal

        self._previous_time: Optional[float] = None
        self._previous_queue: Optional[float] = None
        self._previous_util: Optional[float] = None
        self._previous_rtt: Optional[float] = None

        self._util_history: Deque[float] = deque(maxlen=config.history_samples)
        self._rtt_growth_history: Deque[float] = deque(maxlen=config.history_samples)

        self._pending_candidate: Optional[str] = None
        self._switch_counter = 0

    def _scores(
        self,
        queue_packets: float,
        queue_growth_rate: float,
        utilization: float,
        rtt_growth_rate: float,
    ) -> Dict[str, float]:
        queue_level_n = normalize(
            queue_packets,
            self.cfg.queue_min_packets,
            self.cfg.queue_max_packets,
        )
        queue_growth_n = normalize(
            max(queue_growth_rate, 0.0),
            0.0,
            self.cfg.queue_growth_max_packets_per_sec,
        )

        util_n = normalize(
            utilization,
            self.cfg.utilization_min,
            self.cfg.utilization_max,
        )
        util_persistence = (
            sum(
                1
                for u in self._util_history
                if u >= self.cfg.utilization_persistence_threshold
            )
            / len(self._util_history)
            if self._util_history
            else 0.0
        )

        rtt_growth_n = normalize(
            max(rtt_growth_rate, 0.0),
            self.cfg.rtt_growth_min_ms_per_sec,
            self.cfg.rtt_growth_max_ms_per_sec,
        )
        rtt_persistence = (
            sum(
                1
                for g in self._rtt_growth_history
                if g >= self.cfg.rtt_growth_persistence_threshold_ms_per_sec
            )
            / len(self._rtt_growth_history)
            if self._rtt_growth_history
            else 0.0
        )

        return {
            "QueueScore": clamp01(self.cfg.wq1 * queue_level_n + self.cfg.wq2 * queue_growth_n),
            "UtilScore": clamp01(self.cfg.wu1 * util_n + self.cfg.wu2 * util_persistence),
            "RTTScore": clamp01(self.cfg.wr1 * rtt_growth_n + self.cfg.wr2 * rtt_persistence),
            "queue_level_norm": queue_level_n,
            "queue_growth_norm": queue_growth_n,
            "utilization_norm": util_n,
            "utilization_persistence": util_persistence,
            "rtt_growth_norm": rtt_growth_n,
            "rtt_growth_persistence": rtt_persistence,
        }

    def _apply_hysteresis(self, scores: Dict[str, float]) -> str:
        score_map = {
            "QUEUE": scores["QueueScore"],
            "UTILIZATION": scores["UtilScore"],
            "RTT": scores["RTTScore"],
        }
        candidate = max(self.SIGNALS, key=lambda s: score_map[s])

        if candidate == self.current_signal:
            self._pending_candidate = None
            self._switch_counter = 0
            return self.current_signal

        current_score = score_map[self.current_signal]
        candidate_score = score_map[candidate]

        if candidate_score > current_score + self.cfg.hysteresis_margin:
            if candidate == self._pending_candidate:
                self._switch_counter += 1
            else:
                self._pending_candidate = candidate
                self._switch_counter = 1

            if self._switch_counter >= self.cfg.persistence_samples:
                self.current_signal = candidate
                self._pending_candidate = None
                self._switch_counter = 0
        else:
            self._pending_candidate = None
            self._switch_counter = 0

        return self.current_signal

    def update(
        self,
        time_s: float,
        queue_packets: float,
        utilization: float,
        rtt_ms: float,
    ) -> Dict[str, float | str | bool | int]:
        """Process one measurement sample and return selector state."""
        if self._previous_time is None:
            dt = 1.0
            queue_growth_rate = 0.0
            rtt_growth_rate = 0.0
        else:
            dt = float(time_s) - self._previous_time
            if dt <= 0:
                raise ValueError("time_s must be strictly increasing.")
            queue_growth_rate = (float(queue_packets) - self._previous_queue) / dt
            rtt_growth_rate = (float(rtt_ms) - self._previous_rtt) / dt

        self._util_history.append(float(utilization))
        self._rtt_growth_history.append(max(rtt_growth_rate, 0.0))

        old_signal = self.current_signal
        scores = self._scores(
            queue_packets=float(queue_packets),
            queue_growth_rate=queue_growth_rate,
            utilization=float(utilization),
            rtt_growth_rate=rtt_growth_rate,
        )
        active_signal = self._apply_hysteresis(scores)

        self._previous_time = float(time_s)
        self._previous_queue = float(queue_packets)
        self._previous_util = float(utilization)
        self._previous_rtt = float(rtt_ms)

        return {
            "time": float(time_s),
            "queue_packets": float(queue_packets),
            "utilization": float(utilization),
            "rtt_ms": float(rtt_ms),
            "queue_growth_rate": float(queue_growth_rate),
            "rtt_growth_rate": float(rtt_growth_rate),
            "QueueScore": float(scores["QueueScore"]),
            "UtilScore": float(scores["UtilScore"]),
            "RTTScore": float(scores["RTTScore"]),
            "active_signal": active_signal,
            "switched": active_signal != old_signal,
            "switch_counter": int(self._switch_counter),
        }


def run_selector(rows, config: SelectorConfig):
    policy = SignalSelectionPolicy(config)
    return [
        policy.update(
            time_s=float(row["time"]),
            queue_packets=float(row["queue"]),
            utilization=float(row["utilization"]),
            rtt_ms=float(row["rtt_ms"]),
        )
        for row in rows
    ]
