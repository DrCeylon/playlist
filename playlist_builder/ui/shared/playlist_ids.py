from __future__ import annotations

_HISTORY_PREFIX = "hist-"


def managed_local_playlist_id_from_history(history_session_id: str) -> str:
    """Return the stable managed-playlist key for a history session.

    History session IDs are created as ``hist-{uuid}`` by ``SessionHistoryService``.
    Managed playlists use ``hist-{session_id}`` so the effective key is
    ``hist-hist-{uuid}`` today. A future migration may normalize this double prefix;
    callers must use this helper so the rule stays centralized.
    """
    session_id = history_session_id.strip()
    if not session_id:
        return ""
    return f"{_HISTORY_PREFIX}{session_id}"
