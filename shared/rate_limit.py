"""Request rate limiting for critical paths (scale/security readiness)."""
from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request, status

from shared.settings import get_settings

_settings = get_settings()
_lock = Lock()
_buckets: dict[str, deque[float]] = defaultdict(deque)


def rate_limit_dependency(request: Request) -> None:
    limit = _settings.rate_limit_per_minute
    if limit <= 0:
        return
    client = request.client.host if request.client else "unknown"
    key = f"{client}:{request.url.path}"
    now = time.time()
    window = 60.0
    with _lock:
        q = _buckets[key]
        while q and now - q[0] > window:
            q.popleft()
        if len(q) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="rate limit exceeded",
            )
        q.append(now)
