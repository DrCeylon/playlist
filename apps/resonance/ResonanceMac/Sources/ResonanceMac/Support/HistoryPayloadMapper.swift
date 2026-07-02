import Foundation
import ResonanceCore

enum HistoryPayloadMapper {
    static func generationResult(from payload: BridgeJSONObject) throws -> PlaylistGenerationResult {
        if payload["generation"]?.objectValue != nil {
            return try BridgePayloadBuilder.generationResult(from: payload)
        }
        return try BridgePayloadBuilder.generationResult(from: ["generation": .object(payload)])
    }

    static func importResult(from payload: BridgeJSONObject) throws -> ImportResultState {
        if payload["import"]?.objectValue != nil {
            return try BridgePayloadBuilder.importResult(from: payload)
        }
        return try BridgePayloadBuilder.importResult(from: ["import": .object(payload)])
    }

    static func importOutcomes(from payload: BridgeJSONObject) -> [ImportTrackOutcome] {
        guard let importObject = try? importResult(from: payload) else { return [] }
        return importObject.outcomes
    }
}
