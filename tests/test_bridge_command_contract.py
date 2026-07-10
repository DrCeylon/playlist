from __future__ import annotations

from playlist_builder.ui.bridge.commands import BridgeCommand


def test_bridge_commands_match_swift_contract() -> None:
    """Keep Python BridgeCommand enum aligned with ResonanceCore BridgeCommand."""
    expected = {
        "list_providers",
        "validate_generation_request",
        "generate_playlist",
        "import_playlist",
        "diagnostics",
        "continue_manual_acquisition",
        "list_history",
        "get_history_session",
        "delete_history_session",
        "clear_history",
        "replay_generation",
        "export_history_session",
        "autocomplete_search",
        "probe_manual_acquisition",
        "retry_import_tracks",
        "list_managed_playlists",
        "get_managed_playlist",
        "sync_managed_playlist",
        "plan_sync",
        "list_remote_playlists",
        "get_remote_playlist",
        "import_remote_playlist",
        "apply_sync",
        "provider_auth_status",
        "provider_connect",
        "provider_disconnect",
        "load_remote_playlist_from_file",
        "resolve_sync_conflicts",
    }
    actual = {command.value for command in BridgeCommand}
    assert actual == expected
