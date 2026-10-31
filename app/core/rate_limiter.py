"""In-memory thread-safe sliding window rate limiter for security hardening."""

import time
import threading
from collections import defaultdict
from typing import Dict, List
from fastapi import Request, HTTPException, status


class SlidingWindowRateLimiter:
    """Sliding-window in-memory rate limiter protecting sensitive authentication endpoints."""

    def __init__(self, max_requests: int = 15, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._requests: Dict[str, List[float]] = defaultdict(list)

    def _clean_old_requests(self, client_id: str, current_time: float) -> None:
        threshold = current_time - self.window_seconds
        self._requests[client_id] = [t for t in self._requests[client_id] if t > threshold]

    def check(self, client_id: str) -> bool:
        """Return True if request is allowed, False if limit is exceeded."""
        current_time = time.time()
        with self._lock:
            self._clean_old_requests(client_id, current_time)
            if len(self._requests[client_id]) >= self.max_requests:
                return False
            self._requests[client_id].append(current_time)
            return True

    def reset(self) -> None:
        """Reset internal rate limit tracking (useful for testing)."""
        with self._lock:
            self._requests.clear()


# Default limiter instances
auth_rate_limiter = SlidingWindowRateLimiter(max_requests=10, window_seconds=60)


def rate_limit_auth(request: Request) -> None:
    """Dependency that enforces rate limiting on sensitive auth endpoints."""
    # Identify client by IP or forwarding header
    forwarded = request.headers.get("X-Forwarded-For")
    client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown_client")
    
    if not auth_rate_limiter.check(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication requests. Rate limit exceeded. Please try again in 60 seconds.",
        )
