"""aios_ingest.parser.meeting —— 会议音频 ASR。

- local: 用 whisper.cpp（V2 简化：调 openai-whisper Python 库）
- aliyun: 阿里云一句话识别 REST API
"""
from __future__ import annotations

import io
import logging
import os
import tempfile

from . import BaseParser, ParsedDocument

logger = logging.getLogger("aios_ingest.meeting")


class MeetingParser(BaseParser):
    """会议音频 ASR + 分段。"""

    kind = "meeting"

    def __init__(self, provider: str = "local") -> None:
        self.provider = provider

    def parse(self, content: bytes, filename: str = "") -> ParsedDocument:
        if self.provider == "local":
            return self._parse_local(content, filename)
        elif self.provider == "aliyun":
            return self._parse_aliyun(content, filename)
        else:
            raise ValueError(f"unknown asr provider: {self.provider}")

    def _parse_local(self, content: bytes, filename: str) -> ParsedDocument:
        """V2 简化版：用 openai-whisper Python 库。"""
        try:
            import whisper  # type: ignore
        except ImportError as e:
            raise ValueError(
                "本地 ASR 需安装 openai-whisper: pip install openai-whisper"
            ) from e

        with tempfile.NamedTemporaryFile(suffix=os.path.splitext(filename)[1] or ".mp3", delete=False) as f:
            f.write(content)
            tmp_path = f.name

        try:
            model = whisper.load_model("base")
            result = model.transcribe(tmp_path, verbose=False)
            text = result.get("text", "")
            segments = result.get("segments", [])
            sections = [
                {
                    "title": f"segment-{i}",
                    "content": s.get("text", ""),
                    "level": 2,
                    "start": s.get("start"),
                    "end": s.get("end"),
                }
                for i, s in enumerate(segments)
            ]
            return ParsedDocument(
                kind=self.kind,
                text=text,
                sections=sections,
                metadata={"parser": "whisper-local", "filename": filename, "segment_count": len(segments)},
            )
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _parse_aliyun(self, content: bytes, filename: str) -> ParsedDocument:
        """阿里云一句话识别（V2 stub：上传 OSS + 调 NLS）。"""
        # V2 简化：仅返回占位，V3 接完整链路
        return ParsedDocument(
            kind=self.kind,
            text="[V2 stub] 阿里云 ASR 待 V3 接入",
            metadata={"parser": "aliyun-stub", "filename": filename},
        )


__all__ = ["MeetingParser"]
