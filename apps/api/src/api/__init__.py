"""aios_api —— API v1 路由（参见 02-design-doc.md §2.4）。"""
from . import datasources, health, ingest, ontology, scenarios

__all__ = ["datasources", "health", "ingest", "ontology", "scenarios"]