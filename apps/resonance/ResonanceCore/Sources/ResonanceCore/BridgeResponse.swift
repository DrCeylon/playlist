import Foundation

public struct BridgeResponseMessage: Sendable {
    public let id: String
    public let ok: Bool
    public let result: BridgeJSONObject
    public let error: BridgeErrorPayload?

    public init(id: String, ok: Bool, result: BridgeJSONObject, error: BridgeErrorPayload?) {
        self.id = id
        self.ok = ok
        self.result = result
        self.error = error
    }
}

public struct BridgeEventMessage: Sendable {
    public let id: String
    public let event: BridgeEventType
    public let payload: BridgeJSONObject

    public init(id: String, event: BridgeEventType, payload: BridgeJSONObject) {
        self.id = id
        self.event = event
        self.payload = payload
    }
}

public enum BridgeResponseParser {
    public static func parseResponseLine(_ line: String) throws -> BridgeResponseMessage {
        let object = try parseJSONObject(line)
        guard let id = object["id"]?.stringValue else {
            throw BridgeClientError.invalidResponse
        }
        guard object["type"]?.stringValue == "response" else {
            throw BridgeClientError.invalidResponse
        }
        let ok = object["ok"]?.boolValue ?? false
        let result = object["result"]?.objectValue ?? [:]
        let error = parseError(object["error"]?.objectValue)
        return BridgeResponseMessage(id: id, ok: ok, result: result, error: error)
    }

    public static func parseEventLine(_ line: String) throws -> BridgeEventMessage {
        let object = try parseJSONObject(line)
        guard let id = object["id"]?.stringValue,
              let eventRaw = object["event"]?.stringValue,
              let event = BridgeEventType(rawValue: eventRaw) else {
            throw BridgeClientError.invalidResponse
        }
        let payload = object["payload"]?.objectValue ?? [:]
        return BridgeEventMessage(id: id, event: event, payload: payload)
    }

    public static func parseJSONObject(_ line: String) throws -> BridgeJSONObject {
        let data = Data(line.utf8)
        let value = try JSONSerialization.jsonObject(with: data)
        guard let object = value as? [String: Any] else {
            throw BridgeClientError.invalidResponse
        }
        return try object.mapValues { try BridgeJSONValue(any: $0) }
    }

    private static func parseError(_ object: BridgeJSONObject?) -> BridgeErrorPayload? {
        guard let object,
              let codeRaw = object["code"]?.stringValue,
              let code = BridgeErrorCode(rawValue: codeRaw),
              let message = object["message"]?.stringValue else {
            return nil
        }
        return BridgeErrorPayload(code: code, message: message)
    }
}
