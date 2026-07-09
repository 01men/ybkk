"""aios_api.errors —— 统一错误类型与错误码体系。

设计原则（参见 coding_group/assets/skills/coding-conventions §3）：
  - 每个错误都有错误码（E_XXX_YYY 风格）
  - 错误信息含可读消息 + 上下文
  - 日志格式：[ERROR] [code] message {context}
  - HTTP 响应统一通过中间件转换
"""
from __future__ import annotations

import logging
from enum import Enum
from typing import Any

from fastapi import HTTPException, status

logger = logging.getLogger("aios.errors")


class ErrorCode(str, Enum):
    """平台统一错误码。所有错误必须对应一个 ErrorCode。"""

    # 数据源（E_DS_*）
    E_DS_AUTH = "E_DS_AUTH"
    E_DS_TIMEOUT = "E_DS_TIMEOUT"
    E_DS_NO_PERMISSION = "E_DS_NO_PERMISSION"
    E_DS_NOT_FOUND = "E_DS_NOT_FOUND"
    E_DS_INVALID_SCHEMA = "E_DS_INVALID_SCHEMA"
    E_DS_WRITE_ATTEMPT = "E_DS_WRITE_ATTEMPT"

    # 摄取（E_INGEST_*）
    E_INGEST_UNSUPPORTED = "E_INGEST_UNSUPPORTED"
    E_INGEST_PARSE_FAILED = "E_INGEST_PARSE_FAILED"
    E_INGEST_FILE_TOO_LARGE = "E_INGEST_FILE_TOO_LARGE"
    E_INGEST_EMPTY_RESULT = "E_INGEST_EMPTY_RESULT"

    # 本体（E_ONT_*）
    E_ONT_LOW_CONFIDENCE = "E_ONT_LOW_CONFIDENCE"
    E_ONT_CYPHER_LIMIT_MISSING = "E_ONT_CYPHER_LIMIT_MISSING"
    E_ONT_NOT_FOUND = "E_ONT_NOT_FOUND"

    # 流程（E_FLOW_*）
    E_FLOW_NOT_FOUND = "E_FLOW_NOT_FOUND"
    E_FLOW_INVALID_BINDING = "E_FLOW_INVALID_BINDING"
    E_FLOW_TRIGGER_FAILED = "E_FLOW_TRIGGER_FAILED"

    # 鉴权（E_AUTH_*）
    E_AUTH_UNAUTHORIZED = "E_AUTH_UNAUTHORIZED"
    E_AUTH_FORBIDDEN = "E_AUTH_FORBIDDEN"
    E_AUTH_TOKEN_EXPIRED = "E_AUTH_TOKEN_EXPIRED"
    E_AUTH_REQUIRED = "E_AUTH_REQUIRED"
    E_AUTH_INVALID_CRED = "E_AUTH_INVALID_CRED"
    E_AUTH_TOKEN_INVALID = "E_AUTH_TOKEN_INVALID"

    # 校验（E_VAL_*）
    E_VAL_REQUIRED = "E_VAL_REQUIRED"
    E_VAL_INVALID = "E_VAL_INVALID"
    E_VAL_OUT_OF_RANGE = "E_VAL_OUT_OF_RANGE"

    # 系统（E_SYS_*）
    E_SYS_INTERNAL = "E_SYS_INTERNAL"
    E_SYS_UNAVAILABLE = "E_SYS_UNAVAILABLE"
    E_SYS_TIMEOUT = "E_SYS_TIMEOUT"


class AiosError(Exception):
    """平台统一异常基类。所有业务异常都应继承此类，不直接抛 HTTPException。"""

    code: ErrorCode
    http_status: int
    message: str
    context: dict[str, Any]

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        http_status: int | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.context = context or {}
        # 默认 HTTP 状态：5xx 系统错误 / 4xx 业务错误
        self.http_status = http_status or self._default_http_status(code)

    @staticmethod
    def _default_http_status(code: ErrorCode) -> int:
        if code.value.startswith("E_AUTH_"):
            if code in (
                ErrorCode.E_AUTH_UNAUTHORIZED,
                ErrorCode.E_AUTH_TOKEN_EXPIRED,
                ErrorCode.E_AUTH_REQUIRED,
                ErrorCode.E_AUTH_INVALID_CRED,
                ErrorCode.E_AUTH_TOKEN_INVALID,
            ):
                return status.HTTP_401_UNAUTHORIZED
            return status.HTTP_403_FORBIDDEN
        if code.value.startswith("E_VAL_"):
            return status.HTTP_422_UNPROCESSABLE_ENTITY
        if code.value.startswith(("E_DS_NOT_FOUND", "E_ONT_NOT_FOUND", "E_FLOW_NOT_FOUND")):
            return status.HTTP_404_NOT_FOUND
        if code == ErrorCode.E_SYS_UNAVAILABLE:
            return status.HTTP_503_SERVICE_UNAVAILABLE
        if code == ErrorCode.E_SYS_TIMEOUT:
            return status.HTTP_504_GATEWAY_TIMEOUT
        return status.HTTP_400_BAD_REQUEST

    def to_response(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code.value,
                "message": self.message,
                "context": self.context,
            }
        }

    def log(self) -> None:
        """按规约格式写日志。"""
        logger.error(
            "[%s] %s",
            self.code.value,
            self.message,
            extra={"context": self.context},
        )


# -----------------------------------------------------------------------------
# 常用错误快捷构造
# -----------------------------------------------------------------------------


def datasource_auth(datasource_id: str, **ctx: Any) -> AiosError:
    return AiosError(
        ErrorCode.E_DS_AUTH,
        f"数据源鉴权失败: {datasource_id}",
        context={"datasource_id": datasource_id, **ctx},
    )


def datasource_timeout(datasource_id: str, timeout_s: int, **ctx: Any) -> AiosError:
    return AiosError(
        ErrorCode.E_DS_TIMEOUT,
        f"数据源连接超时（{timeout_s}s）: {datasource_id}",
        context={"datasource_id": datasource_id, "timeout_s": timeout_s, **ctx},
    )


def datasource_no_permission(datasource_id: str, **ctx: Any) -> AiosError:
    return AiosError(
        ErrorCode.E_DS_NO_PERMISSION,
        f"数据源账号权限不足（仅支持只读）: {datasource_id}",
        context={"datasource_id": datasource_id, **ctx},
    )


def ontology_low_confidence(entity_kind: str, confidence: float, **ctx: Any) -> AiosError:
    return AiosError(
        ErrorCode.E_ONT_LOW_CONFIDENCE,
        f"本体推断置信度不足 ({confidence:.2f}): {entity_kind}",
        context={"entity_kind": entity_kind, "confidence": confidence, **ctx},
    )


def ingest_file_too_large(actual_mb: float, limit_mb: int = 200, **ctx: Any) -> AiosError:
    return AiosError(
        ErrorCode.E_INGEST_FILE_TOO_LARGE,
        f"文件超过大小限制 ({actual_mb:.1f}MB > {limit_mb}MB)",
        context={"actual_mb": actual_mb, "limit_mb": limit_mb, **ctx},
    )


def auth_unauthorized(reason: str = "missing or invalid token", **ctx: Any) -> AiosError:
    return AiosError(
        ErrorCode.E_AUTH_UNAUTHORIZED,
        reason,
        context=ctx,
    )


def auth_forbidden(required_role: str, **ctx: Any) -> AiosError:
    return AiosError(
        ErrorCode.E_AUTH_FORBIDDEN,
        f"需要角色: {required_role}",
        context={"required_role": required_role, **ctx},
    )


def re_raise_as_http(err: AiosError) -> HTTPException:
    """将 AiosError 转换为 FastAPI HTTPException。"""
    err.log()
    return HTTPException(status_code=err.http_status, detail=err.to_response()["error"])
