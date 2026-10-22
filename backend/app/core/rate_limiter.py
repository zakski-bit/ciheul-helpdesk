import os
import time
from typing import Dict, List, Optional
from collections import defaultdict
from fastapi import Request, HTTPException, status
from app.core.config import settings

class InMemoryRateLimiter:
    """
    Sliding-window in-memory rate limiter per client IP with spoofing protection
    and bounded memory limits to prevent Denial of Service.
    """
    def __init__(
        self, 
        max_requests: int, 
        window_seconds: int, 
        name: str = "rate_limit", 
        detail: Optional[str] = None,
        max_tracked_ips: int = 10000
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.name = name
        self.detail = detail or f"Terlalu banyak permintaan pada layanan {name}. Harap tunggu sebentar."
        self.max_tracked_ips = max_tracked_ips
        self._records: Dict[str, List[float]] = defaultdict(list)
        self._last_cleanup: float = time.time()

    def _get_client_ip(self, request: Request) -> str:
        direct_ip = request.client.host if request.client and request.client.host else "127.0.0.1"
        # Anti-Spoofing: Only trust X-Forwarded-For if TRUST_PROXY_HEADERS is explicitly enabled
        # AND the direct connecting peer is in the trusted proxy whitelist (e.g., local Nginx or Cloudflare edge).
        if getattr(settings, "TRUST_PROXY_HEADERS", False) and direct_ip in getattr(settings, "TRUSTED_PROXIES", {"127.0.0.1", "::1"}):
            forwarded = request.headers.get("x-forwarded-for")
            if forwarded:
                parts = [p.strip() for p in forwarded.split(",") if p.strip()]
                if parts:
                    return parts[0]
        return direct_ip

    def _cleanup_expired(self, now: float):
        """Purge expired records to ensure memory does not grow unbounded."""
        cutoff = now - self.window_seconds
        keys_to_remove = []
        for key, timestamps in self._records.items():
            valid_ts = [t for t in timestamps if t > cutoff]
            if not valid_ts:
                keys_to_remove.append(key)
            else:
                self._records[key] = valid_ts

        for key in keys_to_remove:
            self._records.pop(key, None)

        # If dictionary size still exceeds capacity, evict the oldest entries
        if len(self._records) > self.max_tracked_ips:
            sorted_keys = sorted(
                self._records.keys(), 
                key=lambda k: max(self._records[k]) if self._records[k] else 0
            )
            excess = len(self._records) - (self.max_tracked_ips // 2)
            for k in sorted_keys[:excess]:
                self._records.pop(k, None)

    def reset(self):
        """Clear all recorded request history (useful for test isolation)."""
        self._records.clear()
        self._last_cleanup = time.time()

    async def __call__(self, request: Request):
        # Allow testing environment to bypass if explicitly configured
        if settings.ENVIRONMENT in ["test", "testing"] and request.headers.get("x-bypass-rate-limit") == "1":
            return

        client_ip = self._get_client_ip(request)
        now = time.time()
        key = f"{self.name}:{client_ip}"

        # Periodic or threshold-based bounded memory cleanup
        if len(self._records) > self.max_tracked_ips or (now - self._last_cleanup > 120):
            self._cleanup_expired(now)
            self._last_cleanup = now

        # Clean expired timestamps outside the current window for this key
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
