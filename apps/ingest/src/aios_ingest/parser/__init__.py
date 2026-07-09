"""aios_ingest.parser —— 多源解析器接口与基类。"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ParsedDocument:
    """解析后的文档抽象表示。"""

    kind: str  # excel | pdf | meeting | doc
    rows: list[dict] = field(default_factory=list)  # 结构化行
    text: str = ""  # 纯文本（用于 LLM 处理）
    sections: list[dict] = field(default_factory=list)  # 段落 [{title, content, level}]
    tables: list[list[list[str]]] = field(default_factory=list)  # 表格
    metadata: dict = field(default_factory=dict)


class BaseParser(ABC):
    """所有解析器基类。"""

    kind: str = "unknown"

    @abstractmethod
    def parse(self, content: bytes, filename: str = "") -> ParsedDocument:
        """从文件字节流解析。"""
        raise NotImplementedError


__all__ = ["ParsedDocument", "BaseParser"]
