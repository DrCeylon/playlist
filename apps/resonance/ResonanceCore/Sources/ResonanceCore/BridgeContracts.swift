import Foundation

public enum BridgeContracts {
    public static func generationRequestDictionary(_ request: PlaylistGenerationRequest) -> [String: Any] {
        var payload: [String: Any] = [
            "name": request.name,
            "provider_id": request.providerID.rawValue,
            "description": request.description,
            "playlist_theme": request.playlistTheme,
            "seeds": request.seeds.map(seedDictionary),
            "keywords": request.keywords,
            "exclusions": request.exclusions.map(exclusionDictionary),
            "energy_curve": energyCurveDictionary(request.energyCurve),
        ]
        if let targetTrackCount = request.targetTrackCount {
            payload["target_track_count"] = targetTrackCount
        }
        if let targetDurationMinutes = request.targetDurationMinutes {
            payload["target_duration_minutes"] = targetDurationMinutes
        }
        return payload
    }

    public static func validationErrorsDictionary(_ result: ValidationResult) -> [String: Any] {
        [
            "valid": result.isValid,
            "errors": result.errors.map { ["field": $0.field, "message": $0.message] },
        ]
    }

    private static func seedDictionary(_ seed: SeedReference) -> [String: Any] {
        [
            "artist": seed.artist,
            "title": seed.title,
            "weight": seed.weight,
        ]
    }

    private static func exclusionDictionary(_ rule: ExclusionRule) -> [String: Any] {
        [
            "kind": rule.kind.rawValue,
            "value": rule.value,
            "reason": rule.reason,
        ]
    }

    private static func energyCurveDictionary(_ curve: EnergyCurveOption) -> [String: Any] {
        [
            "profile": curve.profile.rawValue,
            "chapter_labels": curve.chapterLabels,
        ]
    }
}

public protocol PlaylistGenerationServing: Sendable {
    func validate(request: PlaylistGenerationRequest) -> ValidationResult
    func generate(request: PlaylistGenerationRequest) async throws -> PlaylistGenerationResult
}
