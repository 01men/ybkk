"""aios_flow.metrics —— V3 Prometheus metrics (stdlib-only)."""
from __future__ import annotations

import threading
from collections import defaultdict


class Counter:
    def __init__(self, name: str, doc: str, labels: tuple[str, ...] = ()):
        self.name = name
        self.doc = doc
        self.labels = labels
        self._values: dict[tuple, float] = defaultdict(float)
        self._lock = threading.Lock()

    def inc(self, amount: float = 1.0, **label_values: str) -> None:
        key = tuple(label_values.get(l, "") for l in self.labels)
        with self._lock:
            self._values[key] += amount


class Histogram:
    DEFAULT_BUCKETS: tuple[float, ...] = (
        0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0,
    )

    def __init__(self, name: str, doc: str, labels: tuple[str, ...] = (),
                 buckets: tuple[float, ...] = DEFAULT_BUCKETS):
        self.name = name
        self.doc = doc
        self.labels = labels
        self.buckets = buckets
        self._counts: dict[tuple, dict[float, int]] = {}
        self._sums: dict[tuple, float] = defaultdict(float)
        self._totals: dict[tuple, int] = defaultdict(int)
        self._lock = threading.Lock()

    def observe(self, value: float, **label_values: str) -> None:
        key = tuple(label_values.get(l, "") for l in self.labels)
        with self._lock:
            bucket_dict = self._counts.setdefault(key, {b: 0 for b in self.buckets})
            for b in self.buckets:
                if value <= b:
                    bucket_dict[b] += 1
            self._sums[key] += value
            self._totals[key] += 1


# Flow engine 专用
FLOW_RUN_TOTAL = Counter(
    "aios_flow_run_total",
    "Total flow runs",
    labels=("flow_id", "status"),
)
FLOW_STEP_DURATION = Histogram(
    "aios_flow_step_duration_seconds",
    "Flow step duration",
    labels=("step_id",),
)
LLM_CALL_TOTAL = Counter(
    "aios_llm_call_total",
    "Total LLM calls",
    labels=("provider", "model"),
)
LLM_CALL_DURATION = Histogram(
    "aios_llm_call_duration_seconds",
    "LLM call duration",
    labels=("provider",),
)
LLM_INJECTION_BLOCKED = Counter(
    "aios_llm_injection_blocked_total",
    "LLM injection attempts blocked",
    labels=("actor",),
)


def _format_labels(label_names: tuple[str, ...], key: tuple) -> str:
    if not label_names:
        return ""
    pairs = ",".join(
        f'{ln}="{_escape(kv)}"' for ln, kv in zip(label_names, key)
    )
    return "{" + pairs + "}"


def _escape(v: str) -> str:
    return v.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def render() -> str:
    out: list[str] = []

    for c in (FLOW_RUN_TOTAL, LLM_CALL_TOTAL, LLM_INJECTION_BLOCKED):
        out.append(f"# HELP {c.name} {c.doc}")
        out.append(f"# TYPE {c.name} counter")
        with c._lock:
            items = list(c._values.items())
        for key, value in items:
            lbl = _format_labels(c.labels, key)
            out.append(f"{c.name}{lbl} {value}")

    for h in (FLOW_STEP_DURATION, LLM_CALL_DURATION):
        out.append(f"# HELP {h.name} {h.doc}")
        out.append(f"# TYPE {h.name} histogram")
        with h._lock:
            items = list(h._counts.items())
        for key, bucket_dict in items:
            cumulative = 0
            for b in h.buckets:
                cumulative = bucket_dict.get(b, 0)
                lbl = _format_labels(h.labels + ("le",), key + (str(b),))
                out.append(f"{h.name}_bucket{lbl} {cumulative}")
            lbl = _format_labels(h.labels + ("le",), key + ("+Inf",))
            out.append(f"{h.name}_bucket{lbl} {h._totals.get(key, 0)}")
            out.append(f"{h.name}_sum{_format_labels(h.labels, key)} {h._sums.get(key, 0.0)}")
            out.append(f"{h.name}_count{_format_labels(h.labels, key)} {h._totals.get(key, 0)}")

    return "\n".join(out) + "\n"
