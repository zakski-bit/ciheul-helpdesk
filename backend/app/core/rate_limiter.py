import time
from typing import Dict, List, Optional
from collections import defaultdict
from fastapi import Request, HTTPException, status
from app.core.config import settings

class InMemoryRateLimiter:
    """
    Sliding-window in-memory rate limiter per client IP.
    """
    def __init__(self, max_requests: int, window_seconds: int, name: str = "rate_limit", detail: Optional[str] = None):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.name = name
        self.detail = detail or f"Terlalu banyak permintaan pada layanan {name}. Harap tunggu sebentar."
        self._records: Dict[str, List[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            # First IP in the list is the client IP
            return forwarded.split(",")[0].strip()
        if request.client and request.client.host:
            return request.client.host
        return "127.0.0.1"

    def reset(self):
        """Clear all recorded request history (useful for test isolation)."""
        self._records.clear()

    async def __call__(self, request: Request):
        # Allow testing environment to bypass if explicitly configured
        if settings.ENVIRONMENT in ["test", "testing"] and request.headers.get("x-bypass-rate-limit") == "1":
            return

        client_ip = self._get_client_ip(request)
        now = time.time()
        key = f"{self.name}:{client_ip}"

        # Clean expired timestamps outside the current window
        cutoff = now - self.window_seconds
        history = [t for t in self._records[key] if t > cutoff]

        if len(history) >= self.max_requests:
            oldest = history[0]
            retry_after = max(1, int(oldest + self.window_seconds - now))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=self.detail,
                headers={"Retry-After": str(retry_after)}
            )

        history.append(now)
        self._records[key] = history

import os

# Standard instances for production protection
login_rate_limiter = InMemoryRateLimiter(
    max_requests=int(os.getenv("RATE_LIMIT_LOGIN", "20")), 
    window_seconds=60, 
    name="login", 
    detail="Terlalu banyak percobaan login. Silakan tunggu 1 menit sebelum mencoba lagi."
)

ticket_create_rate_limiter = InMemoryRateLimiter(
    max_requests=int(os.getenv("RATE_LIMIT_TICKETS", "30")), 
    window_seconds=60, 
    name="ticket_creation", 
    detail="Terlalu banyak permintaan pembuatan tiket. Harap tunggu sebelum mengirim tiket baru."
)
