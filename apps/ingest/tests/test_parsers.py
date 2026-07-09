"""aios_ingest.tests.test_parsers —— 4 类解析器单测（不依赖 LLM / 网络）。"""
from __future__ import annotations

import io

import pytest
from openpyxl import Workbook

from aios_ingest.parser.excel import ExcelParser
from aios_ingest.parser.markdown import MarkdownParser


def _make_excel_bytes(rows: list[list]) -> bytes:
    wb = Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.fixture
def excel_bytes() -> bytes:
    return _make_excel_bytes(
        [
            ["物料编码", "物料名称", "规格", "安全库存", "当前库存", "供应商", "仓库"],
            ["M001", "螺栓 M8", "M8x30", 100, 50, "S001", "W01"],
            ["M002", "螺母 M8", "M8", 200, 250, "S001", "W01"],
            ["M003", "垫片", "Φ10", 500, 100, "S002", "W02"],
        ]
    )


def test_excel_parser_basic(excel_bytes: bytes) -> None:
    parser = ExcelParser()
    doc = parser.parse(excel_bytes, "materials.xlsx")
    assert doc.kind == "excel"
    assert len(doc.rows) == 3
    assert doc.rows[0]["物料编码"] == "M001"
    assert doc.metadata["columns"][0]["name"] == "物料编码"
    # 类型推断：安全库存/当前库存 是 number
    col_map = {c["name"]: c["inferred_type"] for c in doc.metadata["columns"]}
    assert col_map["安全库存"] == "number"
    assert col_map["当前库存"] == "number"
    assert col_map["物料编码"] == "string"


def test_excel_parser_empty_sheet() -> None:
    bytes_data = _make_excel_bytes([])
    parser = ExcelParser()
    doc = parser.parse(bytes_data, "empty.xlsx")
    assert doc.rows == []


def test_markdown_parser_sections() -> None:
    md = """# 物料管理规范

## 库存预警

- 当 current_stock < safety_stock 时必须触发预警
- 通知采购员张三

## 来料异常

- IF 收货数量 < 订单数量 THEN 创建 8D 报告
"""
    parser = MarkdownParser()
    doc = parser.parse(md.encode("utf-8"), "spec.md")
    assert doc.kind == "doc"
    titles = [s["title"] for s in doc.sections]
    assert "物料管理规范" in titles
    assert "库存预警" in titles
    # 标准候选
    cands = doc.metadata["standard_candidates"]
    assert any("current_stock" in c["rule"] for c in cands)
    assert any("8D" in c["rule"] for c in cands)


def test_markdown_parser_no_standards() -> None:
    md = "# Hello\n\n普通段落。\n"
    parser = MarkdownParser()
    doc = parser.parse(md.encode("utf-8"), "x.md")
    assert doc.metadata["standard_candidates"] == []


@pytest.mark.skipif(True, reason="需要 openai-whisper 安装且大模型；CI 跳过")
def test_meeting_parser_local() -> None:
    from aios_ingest.parser.meeting import MeetingParser

    p = MeetingParser(provider="local")
    assert p.kind == "meeting"


def test_pdf_parser_invalid() -> None:
    """非 PDF 字节应抛错。"""
    from aios_ingest.parser.pdf import PdfParser

    parser = PdfParser()
    with pytest.raises(Exception):
        parser.parse(b"not a pdf", "fake.pdf")
