"""aios_ontology.tests.test_mapping —— 字段映射单测（纯函数，不依赖 Neo4j）。"""
from __future__ import annotations

from aios_ontology.mapping import auto_map


def test_auto_map_materials() -> None:
    cols = ["物料编码", "物料名称", "规格", "安全库存", "当前库存", "单位"]
    result = auto_map(cols)
    assert "Material" in result
    mapping = result["Material"]
    assert mapping["物料编码"] == "material_code"
    assert mapping["物料名称"] == "material_name"
    assert mapping["规格"] == "spec"
    assert mapping["安全库存"] == "safety_stock"
    assert mapping["当前库存"] == "current_stock"


def test_auto_map_supplier() -> None:
    cols = ["供应商编码", "供应商名称", "supplier_phone"]
    result = auto_map(cols)
    assert "Supplier" in result
    assert result["Supplier"]["供应商编码"] == "supplier_code"


def test_auto_map_warehouse() -> None:
    cols = ["仓库编码", "仓库名称", "仓库地址"]
    result = auto_map(cols)
    assert "Warehouse" in result
    assert result["Warehouse"]["仓库编码"] == "warehouse_code"


def test_auto_map_empty() -> None:
    result = auto_map([])
    assert result == {}


def test_auto_map_no_match() -> None:
    result = auto_map(["价格", "日期", "操作员"])
    # 全没匹配
    assert result == {}
