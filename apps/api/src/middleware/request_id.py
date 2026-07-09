"""request_id 中间件：在每个请求的 state / header 注入 reqId，便于日志关联。"""
from __future__ import annotations

import uuid

from fastapi import FastAPI, Request


def request_id_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def _add_request_id(request: Request, call_next):  # type: ignore[no-untyped-def]
        req_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        request.state.req_id = req_id
        response = await call_next(request)
        response.headers["X-Request-Id"] = req_id
        return response