"""aios_api.middleware —— FastAPI 中间件。

包含：
  - error_handler：AiosError → HTTPException 转换
  - request_id：注入 reqId 用于日志关联
  - audit：关键操作审计
"""
from .error_handler import error_handler_middleware
from .request_id import request_id_middleware

__all__ = ["error_handler_middleware", "request_id_middleware"]