from __future__ import annotations

import ast
from pathlib import Path


def test_youtube_integration_isolated_under_package() -> None:
    forbidden_roots = (
        "playlist_builder/app/playlist_sync",
        "playlist_builder/app/playlist_library",
        "playlist_builder/canonical",
    )
    for root in forbidden_roots:
        for path in Path(root).rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module and "youtube_music" in node.module:
                    raise AssertionError(f"{path} imports {node.module}")
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if "youtube_music" in alias.name or alias.name == "ytmusicapi":
                            raise AssertionError(f"{path} imports {alias.name}")


def test_factory_registers_youtube_without_importing_ytmusicapi(monkeypatch) -> None:
    monkeypatch.setattr(
        "playlist_builder.integration.youtube_music.experimental_guard.is_ytmusicapi_installed",
        lambda: False,
    )
    from playlist_builder.app.factory import build_app_context
    from playlist_builder.canonical.enums import ProviderId

    context = build_app_context()
    assert context.registry.get(ProviderId.YOUTUBE_MUSIC) is not None
