from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class RetryPolicy:
    """Incremental backoff with jitter.

    Delay formula:
        delay = minimum_delay + random(0, minimum_delay)

    The minimum delay increases on each retry and is capped by max_min_delay.
    """

    base_min_delay: float = 2.0
    increment: float = 3.0
    max_min_delay: float = 30.0
    max_attempts: int = 5
    max_total_wait: float = 300.0

    def minimum_delay_for_attempt(self, retry_index: int) -> float:
        if retry_index < 1:
            retry_index = 1
        return min(self.max_min_delay, self.base_min_delay + ((retry_index - 1) * self.increment))

    def delay_for_attempt(self, retry_index: int) -> float:
        minimum = self.minimum_delay_for_attempt(retry_index)
        return minimum + random.uniform(0, minimum)
