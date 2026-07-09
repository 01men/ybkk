"""aios_api.metrics —— V3 Prometheus metrics (stdlib-only, no prometheus_client)."""
from __future__ import annotations

import threading
from collections import defaultdict
from typing import Iterable


class Counter:
    """线程安全 Counter。"""

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
    """线程安全 Histogram（简化：只暴露 count / sum / bucket 边界）。"""

    DEFAULT_BUCKETS: tuple[float, ...] = (
        0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0,
    )

    def __init__(
        self,
        name: str,
        doc: str,
        labels: tuple[str, ...] = (),
        buckets: tuple[float, ...] = DEFAULT_BUCKETS,
    ):
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


class Gauge:
    """线程安全 Gauge。"""

    def __init__(self, name: str, doc: str, labels: tuple[str, ...] = ()):
        self.name = name
        self.doc = doc
        self.labels = labels
        self._values: dict[tuple, float] = {}
        self._lock = threading.Lock()

    def set(self, value: float, **label_values: str) -> None:
        key = tuple(label_values.get(l, "") for l in self.labels)
        with self._lock:
            self._values[key] = value

    def inc(self, amount: float = 1.0, **label_values: str) -> None:
        key = tuple(label_values.get(l, "") for l in self.labels)
        with self._lock:
            self._values[key] = self._values.get(key, 0.0) + amount


# ---- 5 类指标（设计 §5.1） ------------------------------------------------

# 1) API
API_REQUEST_TOTAL = Counter(
    "aios_api_request_total",
    "Total API requests",
    labels=("method", "path", "status"),
)
API_REQUEST_DURATION = Histogram(
    "aios_api_request_duration_seconds",
    "API request duration",
    labels=("method", "path"),
)

# 2) Flow
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

# 3) LLM
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

# 4) Ingest
INGEST_JOB_TOTAL = Counter(
    "aios_ingest_job_total",
    "Total ingest jobs",
    labels=("kind", "status"),
)

# 5) Ontology
ONTOLOGY_NODE_TOTAL = Gauge(
    "aios_ontology_node_total",
    "Total ontology nodes by kind",
    labels=("kind",),
)
OLLAMA_UP = Gauge(
    "aios_ollama_up",
    "1 if ollama is reachable, 0 otherwise",
)


# ---- /metrics 文本渲染 ----------------------------------------------------


def _format_labels(metric_name: str, label_names: tuple[str, ...], key: tuple) -> str:
    if not label_names:
        return ""
    pairs = ",".join(
        f'{ln}="{_escape(kv)}"' for ln, kv in zip(label_names, key)
    )
    return "{" + pairs + "}"


def _escape(v: str) -> str:
    return v.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def render() -> str:
    """渲染 prometheus 文本格式。"""
    out: list[str] = []

    def _emit_counter(c: Counter) -> None:
        out.append(f"# HELP {c.name} {c.doc}")
        out.append(f"# TYPE {c.name} counter")
        with c._lock:
            items = list(c._values.items())
        if not items:
            # 无样本也输出 0 行
            out.append(f"{c.name} 0")
            return
        for key, value in items:
            lbl = _format_labels(c.name, c.labels, key)
            out.append(f"{c.name}{lbl} {value}")

    def _emit_histogram(h: Histogram) -> None:
        out.append(f"# HELP {h.name} {h.doc}")
        out.append(f"# TYPE {h.name} histogram")
        with h._lock:
            items = list(h._counts.items())
        for key, bucket_dict in items:
            cumulative = 0
            for b in h.buckets:
                cumulative = bucket_dict.get(b, 0)
                lbl = _format_labels(
                    h.name,
                    h.labels + ("le",),
                    key + (str(b),),
                )
                out.append(f"{h.name}_bucket{lbl} {cumulative}")
            # +Inf bucket
            lbl = _format_labels(
                h.name,
                h.labels + ("le",),
                key + ("+Inf",),
            )
            out.append(f"{h.name}_bucket{lbl} {h._totals.get(key, 0)}")
            out.append(f"{h.name}_sum{_format_labels(h.name, h.labels, key)} {h._sums.get(key, 0.0)}")
            out.append(
                f"{h.name}_count{_format_labels(h.name, h.labels, key)} {h._totals.get(key, 0)}"
            )

    def _emit_gauge(g: Gauge) -> None:
        out.append(f"# HELP {g.name} {g.doc}")
        out.append(f"# TYPE {g.name} gauge")
        with g._lock:
            items = list(g._values.items())
        for key, value in items:
            lbl = _format_labels(g.name, g.labels, key)
            out.append(f"{g.name}{lbl} {value}")

    for c in (API_REQUEST_TOTAL, FLOW_RUN_TOTAL, LLM_CALL_TOTAL, LLM_INJECTION_BLOCKED, INGEST_JOB_TOTAL):
        _emit_counter(c)
    for h in (API_REQUEST_DURATION, FLOW_STEP_DURATION, LLM_CALL_DURATION):
        _emit_histogram(h)
    for g in (ONTOLOGY_NODE_TOTAL, OLLAMA_UP):
        _emit_gauge(g)

    return "\n".join(out) + "\n"


__all__ = [
    "API_REQUEST_TOTAL",
    "API_REQUEST_DURATION",
    "FLOW_RUN_TOTAL",
    "FLOW_STEP_DURATION",
    "LLM_CALL_TOTAL",
    "LLM_CALL_DURATION",
    "LLM_INJECTION_BLOCKED",
    "INGEST_JOB_TOTAL",
    "ONTOLOGY_NODE_TOTAL",
    "OLLAMA_UP",
    "render",
]
