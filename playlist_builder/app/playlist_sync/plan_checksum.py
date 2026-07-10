from __future__ import annotations

import hashlib
import json

from playlist_builder.ui.shared.dto.playlist_sync import PlaylistSyncPlan


def plan_checksum(plan: PlaylistSyncPlan) -> str:
    """Stable checksum of a sync plan for apply validation."""
    payload = plan.to_dict()
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]
