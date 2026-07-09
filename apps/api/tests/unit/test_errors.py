"""tests.errors —— AiosError 单元测试。

覆盖：5 维场景（不同 code → 不同 http_status + 不同响应格式 + 日志格式）。
"""
from __future__ import annotations

import logging

import pytest

from aios_api.errors import (
    AiosError,
    ErrorCode,
    auth_forbidden,
    auth_unauthorized,
    datasource_auth,
    datasource_no_permission,
    datasource_timeout,
    ingest_file_too_large,
    ontology_low_confidence,
)


class TestErrorCodeMapping:
    """验证 ErrorCode → HTTP status 映射。"""

    @pytest.mark.parametrize(
        ("code", "expected_status"),
        [
            (ErrorCode.E_DS_AUTH, 400),
            (ErrorCode.E_DS_TIMEOUT, 400),
            (ErrorCode.E_DS_NO_PERMISSION, 400),
            (ErrorCode.E_DS_NOT_FOUND, 404),
            (ErrorCode.E_ONT_NOT_FOUND, 404),
            (ErrorCode.E_FLOW_NOT_FOUND, 404),
            (ErrorCode.E_AUTH_UNAUTHORIZED, 401),
            (ErrorCode.E_AUTH_TOKEN_EXPIRED, 401),
            (ErrorCode.E_AUTH_FORBIDDEN, 403),
            (ErrorCode.E_VAL_INVALID, 422),
            (ErrorCode.E_VAL_REQUIRED, 422),
            (ErrorCode.E_SYS_UNAVAILABLE, 503),
            (ErrorCode.E_SYS_TIMEOUT, 504),
            (ErrorCode.E_SYS_INTERNAL, 400),  # 默认 400（不会到这里，由兜底中间件转为 500）
        ],
    )
    def test_http_status_mapping(self, code: ErrorCode, expected_status: int) -> None:
        err = AiosError(code, "test message")
        assert err.http_status == expected_status

    def test_response_shape_contains_code_message_context(self) -> None:
        err = AiosError(
            ErrorCode.E_DS_AUTH,
            "auth failed",
            context={"datasource_id": "ds-123"},
        )
        resp = err.to_response()
        assert resp == {
            "error": {
                "code": "E_DS_AUTH",
                "message": "auth failed",
                "context": {"datasource_id": "ds-123"},
            }
        }

    def test_log_emits_code_and_message(self, caplog: pytest.LogCaptureFixture) -> None:
        err = AiosError(ErrorCode.E_DS_TIMEOUT, "timeout", context={"datasource_id": "ds-1"})
        with caplog.at_level(logging.ERROR, logger="aios.errors"):
            err.log()
        assert "E_DS_TIMEOUT" in caplog.text
        assert "timeout" in caplog.text


class TestErrorFactories:
    """验证便捷工厂函数。"""

    def test_datasource_auth_includes_datasource_id_in_context(self) -> None:
        err = datasource_auth("ds-abc")
        assert err.code == ErrorCode.E_DS_AUTH
        assert err.context["datasource_id"] == "ds-abc"

    def test_datasource_timeout_includes_timeout_value(self) -> None:
        err = datasource_timeout("ds-abc", timeout_s=30)
        assert err.context["timeout_s"] == 30
        assert err.context["datasource_id"] == "ds-abc"

    def test_datasource_no_permission_message_includes_datasource(self) -> None:
        err = datasource_no_permission("ds-xyz")
        assert "ds-xyz" in err.message
        assert "只读" in err.message

    def test_ontology_low_confidence_includes_threshold(self) -> None:
        err = ontology_low_confidence("device", confidence=0.42)
        assert err.code == ErrorCode.E_ONT_LOW_CONFIDENCE
        assert err.context["confidence"] == pytest.approx(0.42)

    def test_ingest_file_too_large_includes_actual_and_limit(self) -> None:
        err = ingest_file_too_large(actual_mb=350.5, limit_mb=200)
        assert err.context["actual_mb"] == pytest.approx(350.5)
        assert err.context["limit_mb"] == 200

    def test_auth_unauthorized_default_message(self) -> None:
        err = auth_unauthorized()
        assert "missing or invalid token" in err.message

    def test_auth_forbidden_includes_required_role(self) -> None:
        err = auth_forbidden(required_role="admin")
        assert err.context["required_role"] == "admin"