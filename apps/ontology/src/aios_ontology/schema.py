"""aios_ontology.schema —— Neo4j 本体 schema（10 节点 + 12 关系 + 索引）。"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NodeKind:
    name: str
    description: str
    required_props: tuple[str, ...]


NODES: tuple[NodeKind, ...] = (
    NodeKind("Material", "物料", ("external_id", "code", "name")),
    NodeKind("Supplier", "供应商", ("external_id", "code", "name")),
    NodeKind("Warehouse", "仓库", ("external_id", "code", "name")),
    NodeKind("Equipment", "设备", ("external_id", "code", "name")),
    NodeKind("Order", "订单", ("external_id", "code", "type")),
    NodeKind("Process", "工艺", ("external_id", "code", "name")),
    NodeKind("ProcessStep", "工艺步骤", ("external_id", "code", "name")),
    NodeKind("DeliveryStandard", "交付标准", ("external_id", "key", "kind")),
    NodeKind("BusinessRule", "业务规则", ("external_id", "content")),
    NodeKind("Role", "角色", ("external_id", "code", "name")),
)

RELATIONSHIPS: tuple[tuple[str, str, str], ...] = (
    ("Material", "SUPPLIED_BY", "Supplier"),
    ("Material", "STORED_IN", "Warehouse"),
    ("Equipment", "MAINTAINED_BY", "Role"),
    ("Process", "HAS_STEP", "ProcessStep"),
    ("ProcessStep", "NEXT", "ProcessStep"),
    ("Order", "USES_MATERIAL", "Material"),
    ("Order", "PRODUCED_BY", "Equipment"),
    ("DeliveryStandard", "APPLIES_TO", "Process"),
    ("DeliveryStandard", "OWNED_BY", "Role"),
    ("BusinessRule", "DEFINES", "DeliveryStandard"),
    ("BusinessRule", "OWNED_BY", "Role"),
    ("Material", "CRITICAL_TO", "Process"),
)

# Cypher 一键初始化
INIT_CYPHER: list[str] = [
    # 索引
    *[f"CREATE INDEX IF NOT EXISTS FOR (n:{k.name}) ON (n.external_id)" for k in NODES],
    # 唯一约束
    *[f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{k.name}) REQUIRE n.external_id IS UNIQUE" for k in NODES],
]


def init_schema(driver) -> None:
    """用驱动执行所有 init cypher。"""
    with driver.session() as session:
        for stmt in INIT_CYPHER:
            session.run(stmt)
