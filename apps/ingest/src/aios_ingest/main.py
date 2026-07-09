"""aios_ingest.main —— 摄取服务 FastAPI。"""
from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from .config import get_settings
from .parser.excel import ExcelParser
from .parser.markdown import MarkdownParser
from .parser.meeting import MeetingParser
from .parser.pdf import PdfParser

logger = logging.getLogger("aios_ingest.api")


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    )
    app.state.settings = settings
    app.state.parsers = {
        "excel": ExcelParser(),
        "pdf": PdfParser(),
        "meeting": MeetingParser(provider=settings.asr_provider),
        "doc": MarkdownParser(),
    }
    logger.info("aios-ingest API 启动")
    yield


app = FastAPI(title="aios-ingest", version="0.2.0", lifespan=lifespan)


class IngestResponse(BaseModel):
    parsed: int
    text_preview: str
    metadata: dict


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


@app.post("/ingest", response_model=IngestResponse)
async def ingest_endpoint(
    kind: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
) -> IngestResponse:
    parser = app.state.parsers.get(kind)
    if parser is None:
        raise HTTPException(status_code=400, detail=f"unknown kind: {kind}")
    content = await file.read()
    try:
        doc = parser.parse(content, file.filename or "unknown")
    except Exception as e:  # noqa: BLE001
        logger.exception("ingest failed")
        raise HTTPException(status_code=422, detail=f"parse error: {e}") from e

    return IngestResponse(
        parsed=len(doc.rows),
        text_preview=doc.text[:2000],
        metadata=doc.metadata,
    )
