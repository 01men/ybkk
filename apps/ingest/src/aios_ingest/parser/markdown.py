"""aios_ingest.parser.markdown —— Markdown 解析器（流程规范）。"""
from __future__ import annotations

import re

from markdown_it import MarkdownIt

from . import BaseParser, ParsedDocument


class MarkdownParser(BaseParser):
    """Markdown 解析：按 # 切分章节。"""

    kind = "doc"

    def parse(self, content: bytes, filename: str = "") -> ParsedDocument:
        text = content.decode("utf-8", errors="ignore")
        md = MarkdownIt()
        tokens = md.parse(text)

        sections: list[dict] = []
        current_title: str | None = None
        current_level: int = 0
        current_content: list[str] = []
        # 标记下一个 inline 是否为标题文字
        expect_title = False
        # 标记：上一个 token 是不是 list_item_open（用来在 inline 后追加 "- "）
        in_list_item = False

        def _flush() -> None:
            nonlocal current_title, current_content
            if current_title is not None:
                sections.append(
                    {
                        "title": current_title,
                        "content": "\n".join(current_content).strip(),
                        "level": current_level,
                    }
                )
            current_title = None
            current_content = []

        for tok in tokens:
            t = tok.type
            if t == "heading_open":
                # 关闭上一节
                _flush()
                # 记录新标题 level
                current_level = int(tok.tag[1]) if tok.tag.startswith("h") else 1
                expect_title = True
            elif t == "heading_close":
                expect_title = False
            elif t == "list_item_open":
                in_list_item = True
            elif t == "list_item_close":
                in_list_item = False
            elif t == "inline":
                inline_text = "".join(c.content for c in (tok.children or []) if c.type == "text")
                if expect_title and current_title is None:
                    if inline_text.strip():
                        current_title = inline_text.strip()
                    expect_title = False
                else:
                    if inline_text:
                        if in_list_item:
                            current_content.append(f"- {inline_text}")
                        else:
                            current_content.append(inline_text)
            elif t == "paragraph_close":
                # 段落结束：补一行空
                if current_content and current_content[-1] != "":
                    current_content.append("")
        # flush last
        _flush()

        # 提取「标准」候选：以 - 开头、含特定关键字的行
        standard_candidates: list[dict] = []
        for sec in sections:
            for line in sec["content"].splitlines():
                m = re.match(r"\s*[-*]\s+(.+)", line)
                if m and any(k in m.group(1) for k in ["必须", "应当", "≤", "≥", ">", "<", "IF", "THEN"]):
                    standard_candidates.append({"section": sec["title"], "rule": m.group(1).strip()})

        return ParsedDocument(
            kind=self.kind,
            text=text,
            sections=sections,
            metadata={
                "parser": "markdown-it",
                "filename": filename,
                "section_count": len(sections),
                "standard_candidates": standard_candidates,
            },
        )


__all__ = ["MarkdownParser"]
