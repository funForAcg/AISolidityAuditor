import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# Simple in-memory rate limiter: max requests per IP per window
_MAX_REQUESTS = 30
_WINDOW_SEC = 60
_hits: dict[str, list[float]] = defaultdict(list)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not request.url.path.startswith("/api/v1/audits") or request.method != "POST":
            return await call_next(request)

        client = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - _WINDOW_SEC

        _hits[client] = [t for t in _hits[client] if t > window_start]

        if len(_hits[client]) >= _MAX_REQUESTS:
            return JSONResponse(
                status_code=429,
                content={"detail": "请求过于频繁，请稍后再试"},
            )

        _hits[client].append(now)
        return await call_next(request)
