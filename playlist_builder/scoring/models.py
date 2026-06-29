from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class MatchScore:
    value: int
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ScoredMatch:
    artist: str
    title: str
    score: MatchScore
    payload: Any = None
