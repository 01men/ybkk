"""aios_ontology.metrics —— V3 Prometheus metrics (stdlib-only)."""
from __future__ import annotations

import threading
from collections import defaultdict


class Gauge:
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


ONTOLOGY_NODE_TOTAL = Gauge(
    "aios_ontology_node_total",
    "Total ontology nodes by kind",
    labels=("kind",),
)
OLLAMA_UP = Gauge(
    "aios_ollama_up",
    "1 if ollama is reachable, 0 otherwise",
)


def _escape(v: str) -> str:
    return v.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def render() -> str:
    out: list[str] = []
    for g in (ONTOLOGY_NODE_TOTAL, OLLAMA_UP):
        out.append(f"# HELP {g.name} {g.doc}")
        out.append(f"# TYPE {g.name} gauge")
        with g._lock:
            items = list(g._values.items())
        for key, value in items:
            if not g.labels:
                out.append(f"{g.name} {value}")
            else:
                pairs = ",".join(f'{ln}="{_escape(kv)}"' for ln, kv in zip(g.labels, key))
                out.append(f"{g.name}{{{pairs}}} {value}")
    return "\n".join(out) + "\n"
