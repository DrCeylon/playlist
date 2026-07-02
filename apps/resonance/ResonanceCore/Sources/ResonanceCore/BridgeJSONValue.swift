import Foundation

public typealias BridgeJSONObject = [String: BridgeJSONValue]

/// Sendable JSON value used by bridge messages to avoid `[String: Any]`.
public enum BridgeJSONValue: Sendable, Equatable {
    case string(String)
    case number(Double)
    case bool(Bool)
    case object(BridgeJSONObject)
    case array([BridgeJSONValue])
    case null

    init(any value: Any) throws {
        switch value {
        case let string as String:
            self = .string(string)
        case let number as NSNumber:
            if CFGetTypeID(number) == CFBooleanGetTypeID() {
                self = .bool(number.boolValue)
            } else {
                self = .number(number.doubleValue)
            }
        case let object as [String: Any]:
            self = .object(try object.mapValues { try BridgeJSONValue(any: $0) })
        case let array as [Any]:
            self = .array(try array.map { try BridgeJSONValue(any: $0) })
        case _ as NSNull:
            self = .null
        default:
            throw BridgeClientError.invalidResponse
        }
    }

    var anyValue: Any {
        switch self {
        case .string(let value):
            return value
        case .number(let value):
            return value
        case .bool(let value):
            return value
        case .object(let value):
            return value.mapValues(\.anyValue)
        case .array(let value):
            return value.map(\.anyValue)
        case .null:
            return NSNull()
        }
    }

    public var stringValue: String? {
        guard case let .string(value) = self else { return nil }
        return value
    }

    public var boolValue: Bool? {
        guard case let .bool(value) = self else { return nil }
        return value
    }

    public var intValue: Int? {
        switch self {
        case .number(let value):
            return Int(value)
        case .string(let value):
            return Int(value)
        default:
            return nil
        }
    }

    public var doubleValue: Double? {
        switch self {
        case .number(let value):
            return value
        case .string(let value):
            return Double(value)
        default:
            return nil
        }
    }

    public var objectValue: BridgeJSONObject? {
        guard case let .object(value) = self else { return nil }
        return value
    }

    public var arrayValue: [BridgeJSONValue]? {
        guard case let .array(value) = self else { return nil }
        return value
    }
}
