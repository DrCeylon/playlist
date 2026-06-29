from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class RateLimiter:
    """Simple sequential limiter to avoid hammering public catalog endpoints."""

    minimum_interval_seconds: float = 2.0
    last_call_at: float = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_call_at
        remaining = self.minimum_interval_seconds - elapsed
        if remaining > 0:
            time.sleep(remaining)
        self.last_call_at = time.monotonic()
