"""aios_ontology.tests.test_schema —— Schema 完整性。"""
from __future__ import annotations

from aios_ontology.schema import NODES, RELATIONSHIPS, INIT_CYPHER


def test_node_count() -> None:
    assert len(NODES) == 10


def test_relationship_count() -> None:
    assert len(RELATIONSHIPS) == 12


def test_all_kinds_referenced() -> None:
    """确保 RELATIONSHIPS 引用的 kind 都在 NODES 里。"""
    kinds = {n.name for n in NODES}
    for src, _, dst in RELATIONSHIPS:
        assert src in kinds, f"unknown src kind: {src}"
        assert dst in kinds, f"unknown dst kind: {dst}"


def test_init_cypher_has_indexes() -> None:
    assert any("CREATE INDEX" in s for s in INIT_CYPHER)
    assert any("CREATE CONSTRAINT" in s for s in INIT_CYPHER)
    # 每个节点类都有索引
    assert len([s for s in INIT_CYPHER if "CREATE INDEX" in s]) == len(NODES)
