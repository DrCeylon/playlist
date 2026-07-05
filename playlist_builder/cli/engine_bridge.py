from __future__ import annotations

import sys
import time

from playlist_builder.app.factory import build_app_context
from playlist_builder.app.settings import AppSettings
from playlist_builder.infrastructure.perf import perf_record, perf_span
from playlist_builder.ui.bridge import JsonRpcEngineBridge, process_json_line
from playlist_builder.app.bridge_runtime import RuntimeEngineBridgeBackend


def _bridge_log(message: str) -> None:
    print(f"resonance-bridge: {message}", file=sys.stderr, flush=True)


def main() -> int:
  """JSON-lines Engine Bridge entry point for Resonance macOS."""
  cold_start_at = time.perf_counter()
  _bridge_log("process started")
  perf_record("bridge", "python_process_start", 0)
  _bridge_log("building app context")
  settings = AppSettings(wait_for_manual_catalog_add=True)
  with perf_span("bridge", "context_build"):
    context = build_app_context(settings)
  with perf_span("bridge", "backend_init"):
    backend = RuntimeEngineBridgeBackend(context)
    bridge = JsonRpcEngineBridge(backend=backend)
  cold_start_ms = int((time.perf_counter() - cold_start_at) * 1000)
  perf_record("bridge", "python_cold_start", cold_start_ms)
  _bridge_log("backend ready, waiting for commands on stdin")

  for line in sys.stdin:
    if not line.strip():
      continue
    _bridge_log(f"command received ({len(line)} bytes)")
    command_started = time.perf_counter()
    for encoded in process_json_line(bridge, line):
      sys.stdout.write(encoded + "\n")
      sys.stdout.flush()
    perf_record(
      "bridge",
      "command_total",
      int((time.perf_counter() - command_started) * 1000),
      metadata={"stdin_bytes": len(line)},
    )
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
