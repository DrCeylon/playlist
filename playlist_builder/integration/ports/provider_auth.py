from __future__ import annotations

from typing import Protocol, runtime_checkable

from playlist_builder.canonical.enums import ProviderId
from playlist_builder.ui.shared.dto.remote_playlist import ProviderAuthState


@runtime_checkable
class ProviderAuthPort(Protocol):
    """Provider authentication boundary — secrets stay outside bridge payloads."""

    @property
    def provider_id(self) -> ProviderId: ...

    def auth_state(self) -> ProviderAuthState: ...

    def connect(self, *, params: dict[str, str]) -> ProviderAuthState: ...

    def disconnect(self) -> ProviderAuthState: ...
