import Foundation

public struct BridgeErrorPayload: Equatable, Sendable {
    public let code: BridgeErrorCode
    public let message: String

    public init(code: BridgeErrorCode, message: String) {
        self.code = code
        self.message = message
    }
}

public struct BridgeResponseMessage: Sendable {
    public let id: String
    public let ok: Bool
    public let result: [String: Any]
    public let error: BridgeErrorPayload?

    public init(id: String, ok: Bool, result: [String: Any], error: BridgeErrorPayload?) {
        self.id = id
        self.ok = ok
        self.result = result
        self.error = error
    }
}

public struct BridgeEventMessage: Sendable {
    public let id: String
    public let event: BridgeEventType
    public let payload: [String: Any]

    public init(id: String, event: BridgeEventType, payload: [String: Any]) {
        self.id = id
        self.event = event
        self.payload = payload
    }
}

public enum BridgeResponseParser {
    public static func parseResponseLine(_ line: String) throws -> BridgeResponseMessage {
        let object = try parseJSONObject(line)
        guard let id = object["id"] as? String else {
            throw BridgeClientError.invalidResponse
        }
        guard object["type"] as? String == "response" else {
            throw BridgeClientError.invalidResponse
        }
        let ok = object["ok"] as? Bool ?? false
        let result = object["result"] as? [String: Any] ?? [:]
        let error = parseError(object["error"] as? [String: Any])
        return BridgeResponseMessage(id: id, ok: ok, result: result, error: error)
    }

    public static func parseEventLine(_ line: String) throws -> BridgeEventMessage {
        let object = try parseJSONObject(line)
        guard let id = object["id"] as? String,
              let eventRaw = object["event"] as? String,
              let event = BridgeEventType(rawValue: eventRaw) else {
            throw BridgeClientError.invalidResponse
        }
        let payload = object["payload"] as? [String: Any] ?? [:]
        return BridgeEventMessage(id: id, event: event, payload: payload)
    }

    public static func parseJSONObject(_ line: String) throws -> [String: Any] {
        let data = Data(line.utf8)
        let value = try JSONSerialization.jsonObject(with: data)
        guard let object = value as? [String: Any] else {
            throw BridgeClientError.invalidResponse
        }
        return object
    }

    private static func parseError(_ object: [String: Any]?) -> BridgeErrorPayload? {
        guard let object,
              let codeRaw = object["code"] as? String,
              let code = BridgeErrorCode(rawValue: codeRaw),
              let message = object["message"] as? String else {
            return nil
        }
        return BridgeErrorPayload(code: code, message: message)
    }
}

public enum BridgeClientError: Error, Equatable {
    case processUnavailable
    case timeout
    case invalidResponse
    case bridgeUnavailable
    case bridge(BridgeErrorPayload)
}
