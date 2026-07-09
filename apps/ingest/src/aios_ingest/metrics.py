"""aios_ingest.metrics —— V3 Prometheus metrics (stdlib-only)."""
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


INGEST_JOB_TOTAL = Counter(
    "aios_ingest_job_total",
    "Total ingest jobs",
    labels=("kind", "status"),
)


def _escape(v: str) -> str:
    return v.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def render() -> str:
    out: list[str] = []
    c = INGEST_JOB_TOTAL
    out.append(f"# HELP {c.name} {c.doc}")
    out.append(f"# TYPE {c.name} counter")
    with c._lock:
        items = list(c._values.items())
    for key, value in items:
        if not c.labels:
            out.append(f"{c.name} {value}")
        else:
            pairs = ",".join(f'{ln}="{_escape(kv)}"' for ln, kv in zip(c.labels, key))
            out.append(f"{c.name}{{{pairs}}} {value}")
    return "\n".join(out) + "\n"
