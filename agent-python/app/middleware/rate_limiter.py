"""
请求限流中间件：基于客户端 IP 的滑动窗口限流。
"""
import logging
import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

# 限流配置
MAX_REQUESTS = 10  # 每个窗口最大请求数
WINDOW_SECONDS = 60  # 滑动窗口大小（秒）


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    简单的滑动窗口限流。只对 POST /chat 端点生效。
    """

    def __init__(self, app, max_requests: int = MAX_REQUESTS, window_seconds: int = WINDOW_SECONDS):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clients: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next) -> Response:
        # 只限流对话接口
        if request.method == "POST" and request.url.path == "/chat":
            client_ip = self._get_client_ip(request)

            if not self._is_allowed(client_ip):
                logger.warning(f"Rate limit exceeded for {client_ip}")
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "请求过于频繁，请稍后再试",
                        "code": 429,
                        "retryAfter": f"{self.window_seconds}s",
                    },
                )

        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    def _is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds

        # 清除过期记录
        timestamps = self.clients[client_ip]
        self.clients[client_ip] = [t for t in timestamps if t > window_start]

        if len(self.clients[client_ip]) >= self.max_requests:
            return False

        self.clients[client_ip].append(now)
        return True
