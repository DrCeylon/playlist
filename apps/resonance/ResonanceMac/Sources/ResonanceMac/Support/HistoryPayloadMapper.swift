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

    static func generationRequest(from payload: BridgeJSONObject) -> PlaylistGenerationRequest? {
        guard !payload.isEmpty else { return nil }

        let name = payload["name"]?.stringValue ?? ""
        let providerRaw = payload["provider_id"]?.stringValue ?? ProviderID.appleMusic.rawValue
        let providerID = ProviderID(rawValue: providerRaw) ?? .appleMusic

        let seedsRaw = payload["seeds"]?.arrayValue ?? []
        let seeds = seedsRaw.compactMap(\.objectValue).map { seed in
            SeedReference(
                artist: seed["artist"]?.stringValue ?? "",
                title: seed["title"]?.stringValue ?? "",
                weight: seed["weight"]?.doubleValue ?? 1.0
            )
        }

        let keywords = (payload["keywords"]?.arrayValue ?? []).compactMap(\.stringValue)
        let description = payload["description"]?.stringValue ?? ""
        let playlistTheme = payload["playlist_theme"]?.stringValue ?? ""
        let targetTrackCount = payload["target_track_count"]?.intValue
        let targetDurationMinutes = payload["target_duration_minutes"]?.intValue

        let energyObject = payload["energy_curve"]?.objectValue ?? [:]
        let profileRaw = energyObject["profile"]?.stringValue ?? EnergyCurveProfile.rising.rawValue
        let profile = EnergyCurveProfile(rawValue: profileRaw) ?? .rising
        let chapterLabels = (energyObject["chapter_labels"]?.arrayValue ?? []).compactMap(\.stringValue)

        let exclusions = (payload["exclusions"]?.arrayValue ?? []).compactMap(\.objectValue).map { item in
            ExclusionRule(
                kind: ExclusionKind(rawValue: item["kind"]?.stringValue ?? "") ?? .artist,
                value: item["value"]?.stringValue ?? "",
                reason: item["reason"]?.stringValue ?? ""
            )
        }

        return PlaylistGenerationRequest(
            name: name,
            providerID: providerID,
            seeds: seeds,
            keywords: keywords,
            description: description,
            targetTrackCount: targetTrackCount,
            targetDurationMinutes: targetDurationMinutes,
            energyCurve: EnergyCurveOption(profile: profile, chapterLabels: chapterLabels),
            exclusions: exclusions,
            playlistTheme: playlistTheme
        )
    }
}
