from __future__ import annotations

import ast
import importlib
import pkgutil
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from playlist_builder.app.factory import build_app_context, get_provider_import_port
from playlist_builder.app.settings import AppSettings
from playlist_builder.canonical.enums import ProviderId
from playlist_builder.canonical.models import CanonicalArtist, CanonicalTrack
from playlist_builder.integration.apple_music.resolver import (
    AppleMusicResolutionOutcome,
    AppleMusicResolutionStatus,
)
from playlist_builder.integration.apple_music.provider_import_port import AppleMusicProviderImportPort
from playlist_builder.integration.ports.provider_import import ProviderImportResolutionStatus

FORBIDDEN_IMPORT_PREFIXES = (
    "playlist_builder.integration.apple_music",
    "playlist_builder.core.applescript",
)

FORBIDDEN_BRIDGE_RUNTIME_TOKENS = (
    "_applescript",
    "AppleMusicResolutionStatus",
    "AppleMusicResolutionOutcome",
    "acquire_song_from_url",
)


def _collect_bridge_runtime_modules() -> list[str]:
    package_path = Path(__file__).resolve().parents[1] / "playlist_builder" / "app" / "bridge_runtime"
    modules: list[str] = []
    for module_info in pkgutil.walk_packages([str(package_path)], prefix="playlist_builder.app.bridge_runtime."):
        if module_info.ispkg:
            continue
        modules.append(module_info.name)
    return modules


def _forbidden_imports_in_file(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                hits.extend(_match_forbidden(alias.name))
        elif isinstance(node, ast.ImportFrom) and node.module:
            hits.extend(_match_forbidden(node.module))
    return hits


def _match_forbidden(module_name: str) -> list[str]:
    return [module_name for prefix in FORBIDDEN_IMPORT_PREFIXES if module_name.startswith(prefix)]


def _forbidden_tokens_in_file(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    return [token for token in FORBIDDEN_BRIDGE_RUNTIME_TOKENS if token in source]


@pytest.mark.parametrize("module_name", _collect_bridge_runtime_modules())
def test_bridge_runtime_module_imports_cleanly(module_name: str):
    importlib.import_module(module_name)


def test_bridge_runtime_has_no_forbidden_provider_imports():
    root = Path(__file__).resolve().parents[1] / "playlist_builder" / "app" / "bridge_runtime"
    offenders: list[str] = []
    for path in root.rglob("*.py"):
        for hit in _forbidden_imports_in_file(path):
            offenders.append(f"{path.name} imports {hit}")
    assert offenders == []


def test_bridge_runtime_has_no_apple_specific_tokens():
    root = Path(__file__).resolve().parents[1] / "playlist_builder" / "app" / "bridge_runtime"
    offenders: list[str] = []
    for path in root.rglob("*.py"):
        for token in _forbidden_tokens_in_file(path):
            offenders.append(f"{path.name} references {token}")
    assert offenders == []


def test_get_provider_import_port_returns_apple_adapter():
    context = build_app_context(AppSettings())
    port = get_provider_import_port(context)
    assert isinstance(port, AppleMusicProviderImportPort)
    assert port.provider_id == ProviderId.APPLE_MUSIC


def test_apple_provider_import_port_maps_resolution_outcomes():
    import_service = MagicMock()
    track = CanonicalTrack(artist=CanonicalArtist(name="Artist"), title="Title")
    apple_outcome = AppleMusicResolutionOutcome(
        track=track,
        persistent_id="PID-1",
        status=AppleMusicResolutionStatus.RESOLVED,
        cache_hit=True,
    )
    import_service.resolver.resolve_batch.return_value = [apple_outcome]
    port = AppleMusicProviderImportPort(import_service)

    outcomes = port.resolve_batch([(track, "Main")])

    assert len(outcomes) == 1
    assert outcomes[0].status == ProviderImportResolutionStatus.RESOLVED
    assert outcomes[0].cache_hit is True
    assert "persistent_id" not in outcomes[0].__dataclass_fields__


def test_apple_provider_import_port_delivers_using_internal_outcomes():
    import_service = MagicMock()
    track = CanonicalTrack(artist=CanonicalArtist(name="Artist"), title="Title")
    apple_outcome = AppleMusicResolutionOutcome(
        track=track,
        persistent_id="PID-1",
        status=AppleMusicResolutionStatus.RESOLVED,
    )
    import_service.resolver.resolve_batch.return_value = [apple_outcome]
    import_service.delivery.sync_playlist.return_value = MagicMock(results=())
    port = AppleMusicProviderImportPort(import_service)
    provider_outcomes = port.resolve_batch([(track, "Main")])

    from playlist_builder.canonical.models import CanonicalPlaylist, CanonicalPlaylistSection

    playlist = CanonicalPlaylist(name="Demo", sections=(CanonicalPlaylistSection(name="Main", tracks=(track,)),))
    port.deliver_playlist(playlist, provider_outcomes)

    import_service.delivery.sync_playlist.assert_called_once()
    delivered = import_service.delivery.sync_playlist.call_args.args[1]
    assert delivered[0].persistent_id == "PID-1"
