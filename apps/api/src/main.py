"""FastAPI 应用入口（V3 含 metrics 端点）。"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api.v1 import (
    health, datasources, auth, flows, flow_runs, audits, scenarios, internal,
    ingest, ontology as ontology_api, llm,
    metrics as metrics_api,
)
from .config import get_settings
from .db import dispose_engine, init_engine
from .middleware import error_handler_middleware, request_id_middleware

logger = logging.getLogger("aios.api")


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    )
    logger.info("aios-api %s 启动（env=%s）", settings.app_version, settings.env)
    init_engine()
    yield
    await dispose_engine()
    logger.info("aios-api 关闭")


def create_app() -> FastAPI:
    app = FastAPI(
        title="元冰可可 AIOS API",
        version="0.4.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 中间件
    request_id_middleware(app)
    error_handler_middleware(app)
    app.middleware("http")(metrics_api.metrics_middleware)  # V3: 自动 metrics

    # 路由
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(datasources.router, prefix="/api/v1")
    app.include_router(scenarios.router, prefix="/api/v1")
    app.include_router(flows.router, prefix="/api/v1")
    app.include_router(flow_runs.router, prefix="/api/v1")
    app.include_router(audits.router, prefix="/api/v1")
    app.include_router(internal.router, prefix="/api/v1")
    # V2
    app.include_router(ingest.router, prefix="/api/v1")
    app.include_router(ontology_api.router, prefix="/api/v1")
    app.include_router(llm.router, prefix="/api/v1")
    # V3
    app.include_router(metrics_api.router)  # /metrics（不需要 /api/v1 前缀，Prometheus 习惯）

    return app


app = create_app()
