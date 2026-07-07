from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from playlist_builder.app.factory import build_app_context
from playlist_builder.app.settings import AppSettings
from playlist_builder.canonical.enums import ProviderId
from playlist_builder.canonical.models import CanonicalTrack


def isolated_manual_settings(tmp_path: Path, **overrides: object) -> AppSettings:
    """AppSettings for manual acquisition tests with an isolated IdentityCache file."""
    return AppSettings(
        wait_for_manual_catalog_add=True,
        identity_cache_path=tmp_path / "identity.json",
        **overrides,
    )


def build_isolated_manual_context(tmp_path: Path, **settings_overrides: object):
    settings = isolated_manual_settings(tmp_path, **settings_overrides)
    context = build_app_context(settings)
    identity_path = settings.identity_cache_path
    assert not identity_path.exists(), (
        f"Expected empty IdentityCache file, found existing cache at {identity_path}"
    )
    return context


def stub_manual_acquisition_prerequisites(applescript: MagicMock) -> None:
    """Force the production acquisition path toward manual OPENED (no library/quick-add)."""
    applescript.collect_candidates_batch = MagicMock(return_value=[[]])
    applescript.try_add_catalog_url = MagicMock(return_value="")
    applescript.open_catalog_url_for_manual = MagicMock()


def assert_identity_cache_miss(context, track: CanonicalTrack, *, provider_id: ProviderId = ProviderId.APPLE_MUSIC) -> None:
    resolver = context.registry.get(provider_id).import_service.resolver
    assert resolver._identity_cache.get(track, provider_id) is None


def install_explicit_manual_interruption_hook(monkeypatch) -> None:
    """Pin ManualAcquisitionGate.hook to the real ManualAcquisitionInterrupted raise."""
    from playlist_builder.app.bridge_runtime.manual_gate import ManualAcquisitionGate

    original_hook = ManualAcquisitionGate.hook

    def explicit_manual_hook(self, track, catalog_candidate, detail) -> None:
        original_hook(self, track, catalog_candidate, detail)

    monkeypatch.setattr(ManualAcquisitionGate, "hook", explicit_manual_hook)
