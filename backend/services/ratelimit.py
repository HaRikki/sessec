"""Tiny in-memory sliding-window rate limiter (per client IP)."""
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

from backend.config import RATE_LIMIT_PER_MINUTE

_hits: dict[str, deque] = defaultdict(deque)


def rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    q = _hits[ip]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= RATE_LIMIT_PER_MINUTE:
        raise HTTPException(status_code=429, detail="Too many requests. Please slow down.")
    q.append(now)
