"""统一错误处理中间件（参见 coding_group/assets/skills/coding-conventions §3）。"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ..errors import AiosError, ErrorCode, re_raise_as_http

logger = logging.getLogger("aios.middleware.error")


def error_handler_middleware(app: FastAPI) -> None:
    """注册统一错误处理。

    - AiosError → 用 err.to_response()
    - RequestValidationError → E_VAL_INVALID 格式
    - 其他异常 → E_SYS_INTERNAL + 隐藏细节
    """

    @app.exception_handler(AiosError)
    async def aios_error_handler(_request: Request, exc: AiosError) -> JSONResponse:
        exc.log()
        return JSONResponse(status_code=exc.http_status, content=exc.to_response())

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # 把 Pydantic 的 errors 包装成平台格式
        wrapped = AiosError(
            ErrorCode.E_VAL_INVALID,
            "请求参数校验失败",
            http_status=422,
            context={"errors": exc.errors()},
        )
        wrapped.log()
        return JSONResponse(status_code=422, content=wrapped.to_response())

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
        # 兜底：隐藏内部细节，只暴露错误码
        wrapped = AiosError(
            ErrorCode.E_SYS_INTERNAL,
            "服务内部错误",
            http_status=500,
            context={"type": type(exc).__name__},
        )
        # 完整堆栈打到日志（但不放进响应）
        logger.exception("[E_SYS_INTERNAL] unhandled exception", exc_info=exc)
        return JSONResponse(status_code=500, content=wrapped.to_response())

    # 防止 unused import 警告
    _ = re_raise_as_http