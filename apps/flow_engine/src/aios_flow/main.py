"""aios_flow.main —— flow_engine 管理 API（启动 workflow / 列出 / 重跑）。"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from temporalio.client import Client

from .config import get_settings
from .triggers.schedule import start_workflow

logger = logging.getLogger("aios_flow.api")


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    )
    app.state.temporal_client = await Client.connect(
        settings.temporal_host, namespace=settings.temporal_namespace
    )
    app.state.settings = settings
    logger.info("aios-flow-engine API 启动")
    yield


app = FastAPI(title="aios-flow-engine", version="0.2.0", lifespan=lifespan)


class StartWorkflowRequest(BaseModel):
    flow_id: str
    scenario_id: str
    flow_template: list[dict] = []
    standard_overrides: dict = {}
    datasource_bindings: dict = {}
    actor: str = "manual"


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


@app.post("/workflows/start")
async def start_workflow_endpoint(req: StartWorkflowRequest) -> dict[str, Any]:
    settings: Any = app.state.settings
    workflow_id = await start_workflow(
        app.state.temporal_client,
        settings.task_queue,
        req.flow_id,
        req.scenario_id,
        req.flow_template,
        req.standard_overrides,
        req.datasource_bindings,
        req.actor,
    )
    return {"workflow_id": workflow_id, "status": "started"}
