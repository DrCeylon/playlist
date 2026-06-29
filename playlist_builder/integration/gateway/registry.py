from __future__ import annotations

from playlist_builder.canonical.contracts import ProviderGateway
from playlist_builder.canonical.enums import ProviderId


class ProviderGatewayRegistry:
    """Registry for provider gateways used by the generic integration layer."""

    def __init__(self) -> None:
        self._gateways: dict[ProviderId, ProviderGateway] = {}

    def register(self, gateway: ProviderGateway) -> None:
        existing = self._gateways.get(gateway.provider_id)
        if existing is not None and existing is not gateway:
            raise ValueError(f"Provider gateway already registered: {gateway.provider_id}")
        self._gateways[gateway.provider_id] = gateway

    def get(self, provider_id: ProviderId) -> ProviderGateway | None:
        return self._gateways.get(provider_id)

    def require(self, provider_id: ProviderId) -> ProviderGateway:
        gateway = self.get(provider_id)
        if gateway is None:
            raise KeyError(f"No provider gateway registered for {provider_id.value}.")
        return gateway

    def list_provider_ids(self) -> tuple[ProviderId, ...]:
        return tuple(self._gateways)
