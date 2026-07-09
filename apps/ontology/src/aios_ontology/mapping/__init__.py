"""aios_ontology.mapping.field_mapper —— 字段映射（Excel 列 → 本体属性）。"""
from __future__ import annotations

import logging
import re

logger = logging.getLogger("aios_ontology.mapping")


# 列名归一化：去空格 / 全小写 / 简繁
def _norm(name: str) -> str:
    return re.sub(r"\s+", "", str(name)).lower()


# 通用映射规则（V2 简化版：正则匹配）
DEFAULT_RULES: list[dict] = [
    {
        "target_kind": "Material",
        "field_map": {
            "_regex_material_code": r"(物料编码|material_?code|^code$|^物料编号)",
            "_regex_material_name": r"(物料名称|material_?name|^name$|^物料名)",
            "_regex_spec": r"(规格|^spec$|型号|model)",
            "_regex_safety_stock": r"(安全库存|safety_?stock|安全存量)",
            "_regex_current_stock": r"(当前库存|current_?stock|current_?qty|库存数|现有库存)",
            "_regex_unit": r"(单位|unit)",
        },
    },
    {
        "target_kind": "Supplier",
        "field_map": {
            "_regex_supplier_code": r"(供应商编码|supplier_?code|供应商号)",
            "_regex_supplier_name": r"(供应商名称|supplier_?name|供应商名)",
        },
    },
    {
        "target_kind": "Warehouse",
        "field_map": {
            "_regex_warehouse_code": r"(仓库编码|warehouse_?code|仓库号)",
            "_regex_warehouse_name": r"(仓库名称|warehouse_?name|仓库名)",
        },
    },
]


def _match(target_pattern: str, col: str) -> bool:
    return bool(re.search(target_pattern, col, re.IGNORECASE))


def auto_map(columns: list[str]) -> dict:
    """根据列名自动映射。返回 {target_kind: {col: ontology_attr}}。"""
    result: dict[str, dict[str, str]] = {}
    for col in columns:
        c = _norm(col)
        for rule in DEFAULT_RULES:
            kind = rule["target_kind"]
            for attr, pattern in rule["field_map"].items():
                if not attr.startswith("_regex_"):
                    continue
                target_attr = attr[len("_regex_"):]  # 去掉 _regex_ 前缀
                if _match(pattern, c):
                    result.setdefault(kind, {})[col] = target_attr
    return result


__all__ = ["auto_map"]
