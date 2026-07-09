"""aios_api.api.v1.ingest —— 摄取任务管理 API（V2）。"""
from __future__ import annotations

import io
import json
import uuid
from datetime import datetime, timezone
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...audit_util import write_audit
from ...db import get_session
from ...middleware.auth import CurrentUser
from ...models import IngestJob

router = APIRouter(prefix="/ingest", tags=["ingest"])


class IngestJobResponse(BaseModel):
    id: str
    kind: str
    filename: str
    status: str
    parsed_count: int
    entities_count: int
    relations_count: int
    error: str | None
    created_by: str
    created_at: datetime
    finished_at: datetime | None


@router.post("/upload", response_model=IngestJobResponse, summary="上传文件并创建摄取任务")
async def upload(
    kind: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> IngestJobResponse:
    if kind not in ("excel", "pdf", "meeting", "doc"):
        raise HTTPException(status_code=400, detail=f"unknown kind: {kind}")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="empty file")

    job = IngestJob(
        id=str(uuid.uuid4()),
        kind=kind,
        filename=file.filename or "unknown",
        minio_path=f"uploads/{job_id_placeholder()}/{file.filename}",  # V2 简化为占位
        status="pending",
        created_by=user["username"],
    )
    job_id_placeholder.reset()  # type: ignore[attr-defined]
    session.add(job)
    await session.commit()
    await session.refresh(job)

    # 同步调 ingest 服务（V2 简化：不等异步 worker）
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(
                "http://ingest:8082/ingest",
                data={"kind": kind},
                files={"file": (file.filename, io.BytesIO(content))},
            )
            r.raise_for_status()
            payload = r.json()
            job.status = "succeeded"
            job.parsed_count = payload.get("parsed", 0)
            job.finished_at = datetime.now(timezone.utc)
            # 如果 kind=excel/pdf/doc，调 ontology 抽取并写入
            if kind in ("excel", "pdf", "doc"):
                text = payload.get("text_preview", "")
                async with httpx.AsyncClient(timeout=60.0) as c2:
                    r2 = await c2.post(
                        "http://ontology:8083/ingest/extract",
                        json={"text": text},
                    )
                    if r2.status_code == 200:
                        extracted = r2.json()
                        entities = extracted.get("entities", [])
                        relations = extracted.get("relations", [])
                        job.entities_count = len(entities)
                        job.relations_count = len(relations)
                        if entities or relations:
                            r3 = await c2.post(
                                "http://ontology:8083/ingest/upsert",
                                json={"entities": entities, "relations": relations},
                            )
                            if r3.status_code != 200:
                                job.error = f"ontology upsert failed: {r3.text[:200]}"
    except Exception as e:  # noqa: BLE001
        job.status = "failed"
        job.error = str(e)[:1000]
        job.finished_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(job)

    # 写审计
    await write_audit(
        session,
        actor=user["username"],
        action=f"ingest.{kind}.{job.status}",
        payload={
            "ingest_id": job.id,
            "filename": job.filename,
            "entities_count": job.entities_count,
            "relations_count": job.relations_count,
        },
    )
    await session.commit()

    return IngestJobResponse(
        id=job.id,
        kind=job.kind,
        filename=job.filename,
        status=job.status,
        parsed_count=job.parsed_count,
        entities_count=job.entities_count,
        relations_count=job.relations_count,
        error=job.error,
        created_by=job.created_by,
        created_at=job.created_at,
        finished_at=job.finished_at,
    )


# ---- 简化版：用一个 thread-local 占位生成器避免 UUID 二次生成 ----------------------


class _JobIdPlaceholder:
    def __init__(self) -> None:
        self._v: str = ""

    def __call__(self) -> str:
        if not self._v:
            self._v = str(uuid.uuid4())
        return self._v

    def reset(self) -> None:
        self._v = ""


job_id_placeholder = _JobIdPlaceholder()  # type: ignore[var-annotated]


@router.get("/jobs", response_model=list[IngestJobResponse], summary="列出摄取任务")
async def list_jobs(
    _user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(50, ge=1, le=200),
) -> list[IngestJobResponse]:
    result = await session.execute(
        select(IngestJob).order_by(IngestJob.created_at.desc()).limit(limit)
    )
    return [
        IngestJobResponse(
            id=j.id,
            kind=j.kind,
            filename=j.filename,
            status=j.status,
            parsed_count=j.parsed_count,
            entities_count=j.entities_count,
            relations_count=j.relations_count,
            error=j.error,
            created_by=j.created_by,
            created_at=j.created_at,
            finished_at=j.finished_at,
        )
        for j in result.scalars().all()
    ]


@router.get("/jobs/{job_id}", response_model=IngestJobResponse, summary="任务详情")
async def get_job(
    job_id: str,
    _user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> IngestJobResponse:
    j = await session.get(IngestJob, job_id)
    if j is None:
        raise HTTPException(status_code=404, detail="job not found")
    return IngestJobResponse(
        id=j.id,
        kind=j.kind,
        filename=j.filename,
        status=j.status,
        parsed_count=j.parsed_count,
        entities_count=j.entities_count,
        relations_count=j.relations_count,
        error=j.error,
        created_by=j.created_by,
        created_at=j.created_at,
        finished_at=j.finished_at,
    )
