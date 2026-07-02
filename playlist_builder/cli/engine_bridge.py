from __future__ import annotations

import sys

from playlist_builder.app.factory import build_app_context
from playlist_builder.app.settings import AppSettings
from playlist_builder.ui.bridge import JsonRpcEngineBridge, process_json_line
from playlist_builder.app.bridge_runtime import RuntimeEngineBridgeBackend


def _bridge_log(message: str) -> None:
    print(f"resonance-bridge: {message}", file=sys.stderr, flush=True)


def main() -> int:
  """JSON-lines Engine Bridge entry point for Resonance macOS."""
  _bridge_log("process started")
  _bridge_log("building app context")
  settings = AppSettings(wait_for_manual_catalog_add=True)
  context = build_app_context(settings)
  backend = RuntimeEngineBridgeBackend(context)
  bridge = JsonRpcEngineBridge(backend=backend)
  _bridge_log("backend ready, waiting for commands on stdin")

  for line in sys.stdin:
    if not line.strip():
      continue
    _bridge_log(f"command received ({len(line)} bytes)")
    for encoded in process_json_line(bridge, line):
      sys.stdout.write(encoded + "\n")
      sys.stdout.flush()
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
