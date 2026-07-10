from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from playlist_builder.app.factory import AppContext
from playlist_builder.observability.api_version import OBSERVABILITY_API_VERSION
from playlist_builder.observability.bus import ObservabilityBus, get_default_bus
from playlist_builder.ui.shared.dto import ProviderOption


class HealthStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass(frozen=True, slots=True)
class HealthCheck:
    id: str
    status: HealthStatus
    message: str
    attributes: tuple[tuple[str, str], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "status": self.status.value,
            "message": self.message,
        }
        if self.attributes:
            payload["attributes"] = {key: value for key, value in self.attributes}
        return payload


def build_health_report(
    context: AppContext,
    *,
    providers: tuple[ProviderOption, ...],
    bus: ObservabilityBus | None = None,
) -> dict[str, Any]:
    """Provider-neutral health snapshot for diagnostics and future API."""
    observability_bus = bus or get_default_bus()
    registered = context.registry.list_provider_ids()
    available = [provider for provider in providers if provider.is_available]
    connected = [provider for provider in providers if provider.is_connected]

    provider_status = HealthStatus.OK
    if registered and not available:
        provider_status = HealthStatus.UNHEALTHY
    elif registered and len(available) < len(registered):
        provider_status = HealthStatus.DEGRADED

    checks = [
        HealthCheck(
            id="engine",
            status=HealthStatus.OK,
            message="Python engine reachable",
        ),
        HealthCheck(
            id="providers",
            status=provider_status,
            message=f"{len(available)} available / {len(registered)} registered",
            attributes=(
                ("registered", str(len(registered))),
                ("available", str(len(available))),
                ("connected", str(len(connected))),
            ),
        ),
        HealthCheck(
            id="observability",
            status=HealthStatus.OK,
            message="Observability bus active",
            attributes=(
                ("event_count", str(observability_bus.event_count())),
                ("api_version", OBSERVABILITY_API_VERSION),
            ),
        ),
    ]

    overall = HealthStatus.OK
    if any(check.status == HealthStatus.UNHEALTHY for check in checks):
        overall = HealthStatus.UNHEALTHY
    elif any(check.status == HealthStatus.DEGRADED for check in checks):
        overall = HealthStatus.DEGRADED

    return {
        "status": overall.value,
        "api_version": OBSERVABILITY_API_VERSION,
        "checks": [check.to_dict() for check in checks],
    }
