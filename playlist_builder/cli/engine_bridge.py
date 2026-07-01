from __future__ import annotations

import sys

from playlist_builder.app.factory import build_app_context
from playlist_builder.app.settings import AppSettings
from playlist_builder.ui.bridge import JsonRpcEngineBridge, process_json_line
from playlist_builder.app.bridge_runtime import RuntimeEngineBridgeBackend


def main() -> int:
  """JSON-lines Engine Bridge entry point for Resonance macOS."""
  settings = AppSettings(wait_for_manual_catalog_add=True)
  context = build_app_context(settings)
  backend = RuntimeEngineBridgeBackend(context)
  bridge = JsonRpcEngineBridge(backend=backend)

  for line in sys.stdin:
    if not line.strip():
      continue
    for encoded in process_json_line(bridge, line):
      sys.stdout.write(encoded + "\n")
      sys.stdout.flush()
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
