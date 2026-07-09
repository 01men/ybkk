"""aios_api.api.v1.metrics —— V3 /metrics 端点（Prometheus 文本格式）。"""
from __future__ import annotations

import time

from fastapi import APIRouter, Request, Response

from ..metrics import API_REQUEST_DURATION, API_REQUEST_TOTAL, render as render_metrics

router = APIRouter()


@router.get("/metrics", include_in_schema=False)
async def metrics_endpoint() -> Response:
    """Prometheus scrape 端点。"""
    return Response(
        content=render_metrics(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


async def metrics_middleware(request: Request, call_next):
    """API 请求中间件：自动 inc counter + observe histogram。"""
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start

    # 排除 /metrics 自身 + /health（避免噪声）
    path = request.url.path
    if path.startswith("/metrics") or path.startswith("/api/v1/health"):
        return response

    # 把 /api/v1/{x}/{y} 归一为 /api/v1/{x}/...（避免高基数）
    norm = _normalize_path(path)

    API_REQUEST_TOTAL.inc(
        method=request.method,
        path=norm,
        status=str(response.status_code),
    )
    API_REQUEST_DURATION.observe(duration, method=request.method, path=norm)
    return response


def _normalize_path(path: str) -> str:
    """把 /api/v1/flows/abc-123/runs 归一为 /api/v1/flows/{id}/runs。"""
    parts = path.split("/")
    out: list[str] = []
    skip_id = False
    for p in parts:
        if skip_id:
            skip_id = False
            continue
        if p and "-" in p and len(p) > 8:
            out.append("{id}")
        else:
            out.append(p)
            # 标记下一个要跳过（路径段后跟 ID）
            if p in {"flows", "flow-runs", "ingest", "ontology", "nodes", "scenarios", "datasources", "audits", "orgs"}:
                skip_id = True
    return "/".join(out)


__all__ = ["router", "metrics_middleware", "_normalize_path"]
