from __future__ import annotations

from datetime import UTC, datetime

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.canonical.models import CanonicalTrack, ProviderIdentity
from playlist_builder.infrastructure.cache.keys import identity_entry_key
from playlist_builder.infrastructure.cache.store import JsonCache


class IdentityCache:
    """Maps canonical track identities to provider-specific external IDs.

    This cache is the persistence layer for the future integration gateway.
    It allows the resolution pipeline to skip repeated provider lookups once a
    canonical track has been resolved for a given platform.
    """

    def __init__(self, store: JsonCache) -> None:
        self.store = store

    def get(self, track: CanonicalTrack, provider_id: ProviderId) -> ProviderIdentity | None:
        payload = self.store.get(identity_entry_key(provider_id, track.identity_key))
        if payload is None:
            return None
        return _deserialize_identity(payload)

    def put(self, track: CanonicalTrack, identity: ProviderIdentity) -> None:
        identity.validate()
        self.store.set(
            identity_entry_key(identity.provider_id, track.identity_key),
            _serialize_identity(identity),
        )

    def put_identity(
        self,
        track: CanonicalTrack,
        *,
        provider_id: ProviderId,
        external_id: str,
        confidence: float,
        resolved_at: datetime | None = None,
    ) -> ProviderIdentity:
        identity = ProviderIdentity(
            provider_id=provider_id,
            external_id=external_id,
            confidence=confidence,
            resolved_at=resolved_at or datetime.now(UTC),
        )
        self.put(track, identity)
        return identity

    def invalidate(self, track: CanonicalTrack, provider_id: ProviderId) -> bool:
        return self.store.delete(identity_entry_key(provider_id, track.identity_key))

    def flush(self) -> None:
        self.store.flush()


def _serialize_identity(identity: ProviderIdentity) -> dict[str, str | float]:
    return {
        "provider_id": identity.provider_id.value,
        "external_id": identity.external_id,
        "confidence": identity.confidence,
        "resolved_at": identity.resolved_at.isoformat(),
    }


def _deserialize_identity(payload: dict[str, object]) -> ProviderIdentity:
    provider_raw = payload.get("provider_id")
    external_id = payload.get("external_id")
    confidence = payload.get("confidence")
    resolved_at_raw = payload.get("resolved_at")

    if not isinstance(provider_raw, str) or not provider_raw.strip():
        raise ValueError("Invalid identity cache payload: provider_id.")
    if not isinstance(external_id, str) or not external_id.strip():
        raise ValueError("Invalid identity cache payload: external_id.")
    if not isinstance(confidence, (int, float)):
        raise ValueError("Invalid identity cache payload: confidence.")
    if not isinstance(resolved_at_raw, str) or not resolved_at_raw.strip():
        raise ValueError("Invalid identity cache payload: resolved_at.")

    return ProviderIdentity(
        provider_id=ProviderId(provider_raw),
        external_id=external_id.strip(),
        confidence=float(confidence),
        resolved_at=datetime.fromisoformat(resolved_at_raw),
    )
