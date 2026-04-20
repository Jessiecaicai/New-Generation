"""
异常上报中间件：捕获 Python 服务的未处理异常，上报到 Java 后端入库。
"""
import logging
import traceback

import httpx
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import get_config

logger = logging.getLogger(__name__)


class ExceptionReporterMiddleware(BaseHTTPMiddleware):
    """
    拦截所有请求，将未捕获的异常上报到 Java 后端的 /api/logs 端点，
    写入 system_logs 表以便在前端日志监控页面展示。
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # 记录本地日志
            logger.error(f"Unhandled exception in {request.method} {request.url.path}: {exc}",
                         exc_info=True)

            # 异步上报到 Java 后端（不阻塞错误响应）
            try:
                await self._report_to_backend(request, exc)
            except Exception as report_err:
                logger.warning(f"Failed to report exception to backend: {report_err}")

            # 重新抛出，让 FastAPI 的全局异常处理器返回 500
            raise

    async def _report_to_backend(self, request: Request, exc: Exception):
        """将异常信息发送到 Java 后端"""
        config = get_config()
        java_url = config.java_backend_url

        if not java_url:
            return

        stack_trace = traceback.format_exception(type(exc), exc, exc.__traceback__)
        stack_str = "".join(stack_trace)
        if len(stack_str) > 4000:
            stack_str = stack_str[:4000] + "\n... (truncated)"

        payload = {
            "serviceName": "PYTHON_AGENT",
            "logLevel": "ERROR",
            "category": type(exc).__name__,
            "message": f"[{request.method} {request.url.path}] {str(exc)}",
            "stackTrace": stack_str,
            "requestId": request.headers.get("X-Request-Id"),
        }

        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(f"{java_url}/api/logs", json=payload)
