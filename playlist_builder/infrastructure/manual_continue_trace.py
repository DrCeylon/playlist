from __future__ import annotations

import sys
import time
from datetime import datetime
from threading import Lock

_TRACE_LOCK = Lock()
_TRACE_LAST_MONO: float | None = None
_TRACE_SESSION_ID = ""


def begin_session(import_session_id: str) -> None:
    global _TRACE_LAST_MONO, _TRACE_SESSION_ID
    with _TRACE_LOCK:
        _TRACE_SESSION_ID = import_session_id.strip()
        _TRACE_LAST_MONO = None
    log(f"BEGIN session import_session_id={import_session_id.strip()}")


def log(message: str) -> None:
    global _TRACE_LAST_MONO
    now_wall = datetime.now()
    now_mono = time.monotonic()
    with _TRACE_LOCK:
        if _TRACE_LAST_MONO is None:
            delta_label = ""
        else:
            delta_ms = max(0, int((now_mono - _TRACE_LAST_MONO) * 1000))
            delta_label = f" (+{delta_ms}ms)"
        _TRACE_LAST_MONO = now_mono
        session_suffix = f" [session={_TRACE_SESSION_ID}]" if _TRACE_SESSION_ID else ""
        timestamp = now_wall.strftime("%H:%M:%S.") + f"{now_wall.microsecond // 1000:03d}"
        line = f"manual-continue-trace: [{timestamp}]{delta_label}{session_suffix} {message}"
        print(line, file=sys.stderr, flush=True)
