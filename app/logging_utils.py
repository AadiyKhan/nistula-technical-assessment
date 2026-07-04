from __future__ import annotations

import logging
import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-Id") or str(uuid4())
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logging.getLogger("nistula.api").info(
            {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            }
        )
        response.headers["X-Request-Id"] = request_id
        response.headers["X-Response-Time-Ms"] = str(duration_ms)
        return response