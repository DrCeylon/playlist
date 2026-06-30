"""Engine Bridge — JSON protocol between SwiftUI shells and the Python engine."""

from playlist_builder.ui.bridge.commands import BridgeCommand, BridgeRequest, BridgeResponse
from playlist_builder.ui.bridge.errors import BridgeError, BridgeErrorCode, InvalidBridgeRequestError
from playlist_builder.ui.bridge.events import BridgeEvent, BridgeEventType
from playlist_builder.ui.bridge.json_rpc import JsonRpcEngineBridge, encode_json_line, process_json_line
from playlist_builder.ui.bridge.protocol import EngineBridge, EngineBridgeBackend

__all__ = [
    "BridgeCommand",
    "BridgeError",
    "InvalidBridgeRequestError",
    "BridgeEvent",
    "BridgeEventType",
    "BridgeRequest",
    "BridgeResponse",
    "EngineBridge",
    "EngineBridgeBackend",
    "JsonRpcEngineBridge",
    "encode_json_line",
    "process_json_line",
]
