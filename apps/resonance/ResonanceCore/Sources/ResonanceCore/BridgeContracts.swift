import Foundation

public enum BridgeContracts {
    public static func generationRequestDictionary(_ request: PlaylistGenerationRequest) -> BridgeJSONObject {
        var payload: BridgeJSONObject = [
            "name": .string(request.name),
            "provider_id": .string(request.providerID.rawValue),
            "description": .string(request.description),
            "playlist_theme": .string(request.playlistTheme),
            "seeds": .array(request.seeds.map(seedDictionary).map(BridgeJSONValue.object)),
            "keywords": .array(request.keywords.map(BridgeJSONValue.string)),
            "exclusions": .array(request.exclusions.map(exclusionDictionary).map(BridgeJSONValue.object)),
            "energy_curve": .object(energyCurveDictionary(request.energyCurve)),
        ]
        if let targetTrackCount = request.targetTrackCount {
            payload["target_track_count"] = .number(Double(targetTrackCount))
        }
        if let targetDurationMinutes = request.targetDurationMinutes {
            payload["target_duration_minutes"] = .number(Double(targetDurationMinutes))
        }
        return payload
    }

    public static func validationErrorsDictionary(_ result: ValidationResult) -> BridgeJSONObject {
        [
            "valid": .bool(result.isValid),
            "errors": .array(result.errors.map {
                .object(["field": .string($0.field), "message": .string($0.message)])
            }),
        ]
    }

    private static func seedDictionary(_ seed: SeedReference) -> BridgeJSONObject {
        [
            "artist": .string(seed.artist),
            "title": .string(seed.title),
            "weight": .number(seed.weight),
        ]
    }

    private static func exclusionDictionary(_ rule: ExclusionRule) -> BridgeJSONObject {
        [
            "kind": .string(rule.kind.rawValue),
            "value": .string(rule.value),
            "reason": .string(rule.reason),
        ]
    }

    private static func energyCurveDictionary(_ curve: EnergyCurveOption) -> BridgeJSONObject {
        [
            "profile": .string(curve.profile.rawValue),
            "chapter_labels": .array(curve.chapterLabels.map(BridgeJSONValue.string)),
        ]
    }
}

public protocol PlaylistGenerationServing: Sendable {
    func validate(request: PlaylistGenerationRequest) -> ValidationResult
    func generate(request: PlaylistGenerationRequest) async throws -> PlaylistGenerationResult
}
